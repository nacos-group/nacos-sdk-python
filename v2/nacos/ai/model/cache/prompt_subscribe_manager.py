import asyncio
from typing import Callable, Awaitable, List, Optional

from v2.nacos.ai.model.prompt.prompt import Prompt
from v2.nacos.ai.util.prompt_util import build_prompt_cache_key


class PromptSubscribeManager:

	def __init__(self):
		self.subscribers: dict[str, List[Callable[[str, Prompt], Awaitable[None]]]] = {}
		self.lock = asyncio.Lock()

	async def register_subscriber(self, prompt_key: str, version: Optional[str],
			label: Optional[str],
			callback_func: Callable[[str, Prompt], Awaitable[None]]):
		key = build_prompt_cache_key(prompt_key, version, label)
		async with self.lock:
			if key not in self.subscribers:
				self.subscribers[key] = []
			self.subscribers[key].append(callback_func)

	async def deregister_subscriber(self, prompt_key: str, version: Optional[str],
			label: Optional[str],
			callback_func: Callable[[str, Prompt], Awaitable[None]]):
		if not callback_func:
			return
		key = build_prompt_cache_key(prompt_key, version, label)
		async with self.lock:
			if key not in self.subscribers:
				return
			self.subscribers[key] = [func for func in self.subscribers[key] if func != callback_func]
			if not self.subscribers[key]:
				del self.subscribers[key]

	def is_subscribed(self, prompt_key: str, version: Optional[str],
			label: Optional[str]) -> bool:
		key = build_prompt_cache_key(prompt_key, version, label)
		if key not in self.subscribers:
			return False
		return len(self.subscribers[key]) > 0
