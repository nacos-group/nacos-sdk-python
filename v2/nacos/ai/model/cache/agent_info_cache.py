import asyncio
import logging
from typing import Dict, Optional

from v2.nacos.ai.model.a2a.a2a import AgentCardDetailInfo
from v2.nacos.ai.model.cache.agent_subscribe_manager import \
	AgentSubscribeManager
from v2.nacos.ai.util.agent_util import build_agent_key
from v2.nacos.common.constants import Constants


class AgentInfoCacheHolder:

	def __init__(self, subscribe_manager: AgentSubscribeManager, ai_proxy):
		self.agent_subscribe_manager = subscribe_manager
		self.agent_card_cache: Dict[str, AgentCardDetailInfo] = {}
		self.cache_lock = asyncio.Lock()
		self.logger = logging.getLogger(Constants.AI_MODULE)
		self.task : Dict[str, asyncio.Task] = {}

		from v2.nacos.ai.remote.ai_grpc_client_proxy import AIGRPCClientProxy
		if not isinstance(ai_proxy, AIGRPCClientProxy):
			raise TypeError(
					"ai_proxy must be AIGRPCClientProxy instance")
		self.ai_proxy = ai_proxy


	async def shutdown(self):
		for task in self.task.values():
			task.cancel()
		for task in self.task.values():
			try:
				await task
			except asyncio.CancelledError:
				pass
		self.task.clear()

	async def add_agent_update_task(self,agent_name:str ,version:str):
		key = build_agent_key(agent_name,version)
		if key not in self.task:
			self.task[key] = asyncio.create_task(self.update_agent(agent_name,version))

	async def remove_agent_update_task(self,agent_name:str ,version:str):
		key = build_agent_key(agent_name, version)
		if key in self.task:
			self.task[key].cancel()
			try:
				await self.task[key]
			except asyncio.CancelledError:
				pass
			del self.task[key]

	async def update_agent(self,agent_name:str,version:str):
		while True:
			try:
				agent_card_detail = await self.ai_proxy.get_agent_card(agent_name, version,  "")
				await self.process_agent_card_detail_info(agent_card_detail)
			except Exception as e:
				self.logger.error(
						f"query agent card error: {agent_name} -> {version},{e}")

			try:
				await asyncio.sleep(10)
			except asyncio.TimeoutError:
				continue

	async def get_agent_card(self, agent_name: str, version: str) -> Optional[
		AgentCardDetailInfo]:
		key = build_agent_key(agent_name, version)
		async with self.cache_lock:
			if key in self.agent_card_cache:
				return self.agent_card_cache[key]
			else:
				return None

	async def process_agent_card_detail_info(self,
			agent_card_detail_info: AgentCardDetailInfo):
		agent_name = agent_card_detail_info.name
		version = agent_card_detail_info.version
		is_latest = agent_card_detail_info.latest_version
		key = build_agent_key(agent_name, version)
		async with self.cache_lock:
			old_agent_card = self.agent_card_cache.get(key)
			self.agent_card_cache[key] = agent_card_detail_info
			if is_latest is not None and is_latest:
				latest_key = build_agent_key(agent_name, None)
				self.agent_card_cache[latest_key] = agent_card_detail_info

		if old_agent_card is None or self.is_agent_changed(old_agent_card,
																agent_card_detail_info):
			for callback_func in self.agent_subscribe_manager.subscribers.get(
					key, []):
				await callback_func(agent_card_detail_info.name,
									agent_card_detail_info)
			if is_latest is not None and is_latest:
				for callback_func in self.agent_subscribe_manager.subscribers.get(
						latest_key, []):
					await callback_func(agent_card_detail_info.name,
										agent_card_detail_info)

	def is_agent_changed(self, old_agent_card: AgentCardDetailInfo,
			new_agent_card: AgentCardDetailInfo):
		new_agent_card_str = new_agent_card.model_dump_json()
		if old_agent_card is None:
			self.logger.info(
					f"init new agent card: {new_agent_card.name} -> {new_agent_card_str}")
			return True
		old_agent_card_str = old_agent_card.model_dump_json()
		if old_agent_card_str != new_agent_card_str:
			self.logger.info(
					f"agent card changed: {new_agent_card.name} -> {new_agent_card_str}")
			return True
		else:
			return False