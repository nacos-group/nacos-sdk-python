import asyncio
from typing import Callable, Awaitable, List

from v2.nacos.ai.model.mcp.mcp import McpServerDetailInfo
from v2.nacos.ai.util.mcp_server_util import build_mcp_server_key


class McpServerSubscribeManager:

	def __init__(self):
		self.subscribers: dict[str, List[Callable[[str, str, str, McpServerDetailInfo], Awaitable[None]]]] = {}
		self.lock = asyncio.Lock()

	async def register_subscriber(self,mcp_name:str, version:str, callback_func: Callable[[str, str, str, McpServerDetailInfo], Awaitable[None]]):
		key = build_mcp_server_key(mcp_name, version)
		async with self.lock:
			if key not in self.subscribers:
				self.subscribers[key] = []
			self.subscribers[key].append(callback_func)

	async def deregister_subscriber(self, mcp_name:str, version:str, callback_func: Callable[[str, str, str, McpServerDetailInfo], Awaitable[None]]):
		if not callback_func:
			return
		key = build_mcp_server_key(mcp_name, version)
		async with self.lock:
			if key not in self.subscribers:
				return
			self.subscribers[key] = [func for func in self.subscribers[key] if func != callback_func]
			if not self.subscribers[key]:
				del self.subscribers[key]

	async def is_subscribed(self, mcp_name:str, version:str) -> bool:
		key = build_mcp_server_key(mcp_name, version)
		if key not in self.subscribers:
			return False
		return len(self.subscribers[key]) > 0
