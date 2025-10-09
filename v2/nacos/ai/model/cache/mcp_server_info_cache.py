import asyncio
import logging
from typing import Dict, Optional

from v2.nacos.ai.model.cache.mcp_server_subscribe_manager import \
	McpServerSubscribeManager
from v2.nacos.ai.model.mcp.mcp import McpServerDetailInfo
from v2.nacos.ai.util.mcp_server_util import build_mcp_server_key
from v2.nacos.common.constants import Constants


class McpServerInfoCacheHolder:

	def __init__(self, subscribe_manager: McpServerSubscribeManager, ai_proxy):
		self.mcp_server_subscribe_manager = subscribe_manager
		self.mcp_server_cache: Dict[str, McpServerDetailInfo] = {}
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

	async def add_mcp_server_update_task(self,mcp_name:str ,version:str):
		key = build_mcp_server_key(mcp_name,version)
		if key not in self.task:
			self.task[key] = asyncio.create_task(self.update_mcp_server(mcp_name,version))

	async def remove_mcp_server_update_task(self,mcp_name:str ,version:str):
		key = build_mcp_server_key(mcp_name, version)
		if key in self.task:
			self.task[key].cancel()
			try:
				await self.task[key]
			except asyncio.CancelledError:
				pass
			del self.task[key]

	async def update_mcp_server(self,mcp_name:str,version:str):
		while True:
			try:
				mcp_server_detail = await self.ai_proxy.query_mcp_server(mcp_name, version)
				await self.process_mcp_server_detail_info(mcp_server_detail)
			except Exception as e:
				self.logger.error(
						f"query mcp server error: {mcp_name} -> {version},{e}")

			try:
				await asyncio.sleep(10)
			except asyncio.TimeoutError:
				continue

	async def get_mcp_server(self, mcp_name: str, version: str) -> Optional[
		McpServerDetailInfo]:
		key = build_mcp_server_key(mcp_name, version)
		async with self.cache_lock:
			if key in self.mcp_server_cache:
				return self.mcp_server_cache[key]
			else:
				return None

	async def process_mcp_server_detail_info(self,
			mcp_server_detail_info: McpServerDetailInfo):
		mcp_name = mcp_server_detail_info.name
		version = mcp_server_detail_info.versionDetail.version
		is_latest = mcp_server_detail_info.versionDetail.is_latest
		key = build_mcp_server_key(mcp_name, version)
		async with self.cache_lock:
			old_mcp_server = self.mcp_server_cache.get(key)
			self.mcp_server_cache[key] = mcp_server_detail_info
			if is_latest is not None and is_latest:
				latest_key = build_mcp_server_key(mcp_name, None)
				self.mcp_server_cache[latest_key] = mcp_server_detail_info

		if old_mcp_server is None or self.is_mcp_server_changed(old_mcp_server,
																mcp_server_detail_info):
			for callback_func in self.mcp_server_subscribe_manager.subscribers.get(
					key, []):
				await callback_func(mcp_server_detail_info.id,
									mcp_server_detail_info.namespaceId,
									mcp_server_detail_info.name,
									mcp_server_detail_info)
			if is_latest is not None and is_latest:
				for callback_func in self.mcp_server_subscribe_manager.subscribers.get(
						latest_key, []):
					await callback_func(mcp_server_detail_info.id,
										mcp_server_detail_info.namespaceId,
										mcp_server_detail_info.name,
										mcp_server_detail_info)

	def is_mcp_server_changed(self, old_mcp_server: McpServerDetailInfo,
			new_mcp_server: McpServerDetailInfo):
		new_mcp_server_str = new_mcp_server.model_dump_json()
		if old_mcp_server is None:
			self.logger.info(
					f"init new mcp service: {new_mcp_server.name} -> {new_mcp_server_str}")
			return True
		old_mcp_server_str = old_mcp_server.model_dump_json()
		if old_mcp_server_str != new_mcp_server_str:
			self.logger.info(
					f"mcp service changed: {new_mcp_server.name} -> {new_mcp_server_str}")
			return True
		else:
			return False