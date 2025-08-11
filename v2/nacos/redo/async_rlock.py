import asyncio
from typing import Optional


class AsyncRLock:
	"""
	异步可重入锁，支持超时和更完整的功能
	"""

	def __init__(self):
		self._lock = asyncio.Lock()
		self._owner: Optional[asyncio.Task] = None
		self._count = 0
		# 用于调试和监控
		self._acquire_stack = []

	async def acquire(self, timeout: Optional[float] = None) -> bool:
		"""
		获取锁

		Args:
			timeout: 超时时间，None表示无限等待

		Returns:
			bool: 是否成功获取锁
		"""
		current_task = asyncio.current_task()

		# 如果当前任务已经持有锁
		if self._owner == current_task:
			self._count += 1
			return True

		# 尝试获取底层锁
		try:
			if timeout is not None:
				await asyncio.wait_for(self._lock.acquire(), timeout=timeout)
			else:
				await self._lock.acquire()

			self._owner = current_task
			self._count = 1
			return True
		except asyncio.TimeoutError:
			return False

	def release(self):
		"""释放锁"""
		current_task = asyncio.current_task()

		if self._owner != current_task:
			raise RuntimeError("Cannot release un-acquired lock")

		self._count -= 1
		if self._count == 0:
			self._owner = None
			self._lock.release()

	def locked(self) -> bool:
		"""检查锁是否被持有"""
		return self._lock.locked()

	def owned(self) -> bool:
		"""检查当前任务是否持有锁"""
		return self._owner == asyncio.current_task()

	async def __aenter__(self):
		await self.acquire()
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		self.release()