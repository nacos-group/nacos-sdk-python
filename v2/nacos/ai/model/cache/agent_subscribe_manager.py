import asyncio
from typing import Callable, Awaitable, List

from a2a.types import AgentCard

from v2.nacos.ai.model.a2a.a2a import AgentCardDetailInfo
from v2.nacos.ai.util.agent_util import build_agent_key


class AgentSubscribeManager:

	def __init__(self):
		self.subscribers: dict[str, List[Callable[[str, AgentCardDetailInfo], Awaitable[None]]]] = {}
		self.lock = asyncio.Lock()

	async def register_subscriber(self,agent_name:str, version:str, callback_func: Callable[[str, AgentCardDetailInfo], Awaitable[None]]):
		key = build_agent_key(agent_name, version)
		async with self.lock:
			if key not in self.subscribers:
				self.subscribers[key] = []
			self.subscribers[key].append(callback_func)

	async def deregister_subscriber(self, agent_name:str, version:str, callback_func: Callable[[str, AgentCardDetailInfo], Awaitable[None]]):
		if not callback_func:
			return
		key = build_agent_key(agent_name, version)
		async with self.lock:
			if key not in self.subscribers:
				return
			self.subscribers[key] = [func for func in self.subscribers[key] if func != callback_func]
			if not self.subscribers[key]:
				del self.subscribers[key]

	async def is_subscribed(self, agent_name:str, version:str) -> bool:
		key = build_agent_key(agent_name, version)
		if key not in self.subscribers:
			return False
		return len(self.subscribers[key]) > 0
