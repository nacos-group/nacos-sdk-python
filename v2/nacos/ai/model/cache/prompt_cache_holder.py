import asyncio
import logging
from typing import Dict, Optional

from v2.nacos.ai.model.cache.prompt_subscribe_manager import PromptSubscribeManager
from v2.nacos.ai.model.prompt.prompt import Prompt
from v2.nacos.ai.util.prompt_util import build_prompt_cache_key
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, NOT_FOUND, NOT_MODIFIED

DEFAULT_PROMPT_UPDATE_INTERVAL = 10


class PromptCacheHolder:

	def __init__(self, subscribe_manager: PromptSubscribeManager, ai_client_proxy,
			update_interval: float = DEFAULT_PROMPT_UPDATE_INTERVAL):
		"""
		Args:
			subscribe_manager: Manager for prompt change subscribers
			ai_client_proxy: Any object with async query_prompt(prompt_key, version, label, md5) method.
				Can be AIGRPCClientProxy or AiHttpClientProxy.
			update_interval: Poll interval in seconds (default 10s)
		"""
		self.prompt_subscribe_manager = subscribe_manager
		self.ai_client_proxy = ai_client_proxy
		self.update_interval = update_interval
		self.prompt_cache: Dict[str, Prompt] = {}
		self.cache_lock = asyncio.Lock()
		self.logger = logging.getLogger(Constants.AI_MODULE)
		self.tasks: Dict[str, asyncio.Task] = {}

	async def shutdown(self):
		for task in self.tasks.values():
			task.cancel()
		for task in self.tasks.values():
			try:
				await task
			except asyncio.CancelledError:
				pass
		self.tasks.clear()

	async def subscribe_prompt(self, prompt_key: str, version: Optional[str],
			label: Optional[str]) -> Optional[Prompt]:
		cache_key = build_prompt_cache_key(prompt_key, version, label)
		prompt = None
		try:
			prompt = await self.ai_client_proxy.query_prompt(prompt_key, version, label, None)
			self._process_prompt(prompt_key, cache_key, prompt)
		except NacosException as e:
			if e.error_code != NOT_FOUND:
				raise
			self._process_prompt(prompt_key, cache_key, None)

		self._add_update_task(prompt_key, version, label)
		self.logger.info(f"Subscribed prompt: {prompt_key}, version: {version}, label: {label}")
		return prompt

	def unsubscribe_prompt(self, prompt_key: str, version: Optional[str],
			label: Optional[str]):
		cache_key = build_prompt_cache_key(prompt_key, version, label)
		self._remove_update_task(prompt_key, version, label)
		self.prompt_cache.pop(cache_key, None)
		self.logger.info(f"Unsubscribed prompt: {prompt_key}, version: {version}, label: {label}")

	def get_cached_prompt(self, prompt_key: str, version: Optional[str],
			label: Optional[str]) -> Optional[Prompt]:
		cache_key = build_prompt_cache_key(prompt_key, version, label)
		return self.prompt_cache.get(cache_key)

	def _add_update_task(self, prompt_key: str, version: Optional[str],
			label: Optional[str]):
		cache_key = build_prompt_cache_key(prompt_key, version, label)
		if cache_key not in self.tasks:
			self.tasks[cache_key] = asyncio.create_task(
				self._update_prompt_loop(prompt_key, version, label, cache_key))

	def _remove_update_task(self, prompt_key: str, version: Optional[str],
			label: Optional[str]):
		cache_key = build_prompt_cache_key(prompt_key, version, label)
		task = self.tasks.pop(cache_key, None)
		if task is not None:
			task.cancel()

	async def _update_prompt_loop(self, prompt_key: str, version: Optional[str],
			label: Optional[str], cache_key: str):
		while True:
			try:
				await asyncio.sleep(self.update_interval)
			except asyncio.CancelledError:
				return

			try:
				current_prompt = self.prompt_cache.get(cache_key)
				current_md5 = current_prompt.md5 if current_prompt else None
				latest_prompt = await self.ai_client_proxy.query_prompt(
					prompt_key, version, label, current_md5)
				self._process_prompt(prompt_key, cache_key, latest_prompt)
			except NacosException as e:
				if e.error_code == NOT_FOUND:
					self._process_prompt(prompt_key, cache_key, None)
				elif e.error_code == NOT_MODIFIED:
					pass
				else:
					self.logger.warning(
						f"Prompt updater query failed: promptKey={prompt_key}, err={e.message}")
			except asyncio.CancelledError:
				return
			except Exception as e:
				self.logger.warning(
					f"Prompt updater unexpected error: promptKey={prompt_key}, err={e}")

	def _process_prompt(self, prompt_key: str, cache_key: str,
			new_prompt: Optional[Prompt]):
		old_prompt = self.prompt_cache.get(cache_key)
		if new_prompt is None:
			self.prompt_cache.pop(cache_key, None)
		else:
			self.prompt_cache[cache_key] = new_prompt

		if self._is_prompt_changed(old_prompt, new_prompt):
			subscribers = self.prompt_subscribe_manager.subscribers.get(cache_key, [])
			for callback_func in subscribers:
				try:
					asyncio.ensure_future(callback_func(prompt_key, new_prompt))
				except Exception as e:
					self.logger.error(f"Prompt change callback error: {e}")

	@staticmethod
	def _is_prompt_changed(old_prompt: Optional[Prompt],
			new_prompt: Optional[Prompt]) -> bool:
		old_json = "" if old_prompt is None else old_prompt.model_dump_json()
		new_json = "" if new_prompt is None else new_prompt.model_dump_json()
		return old_json != new_json
