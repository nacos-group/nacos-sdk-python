import asyncio
import logging
from abc import abstractmethod, ABC
from typing import Dict, Set, Optional

from v2.nacos.redo.async_rlock import AsyncRLock
from v2.nacos.redo.redo_data import RedoData
from v2.nacos.transport.connection_event_listener import ConnectionEventListener


class AbstractRedoService(ConnectionEventListener,ABC):

	def __init__(self, module:str):
		self._module = module
		self._logger = logging.getLogger(module)
		self._connected : bool  = False
		self._stop_event = asyncio.Event()
		self._execute_redo_channel = asyncio.Queue()
		self._listen_task = asyncio.create_task(self._execute_redo_task())
		self._redo_data_map : Dict[str, Dict[str, RedoData]] = {}
		self._locks: Dict[str, AsyncRLock] = {}

	async def on_connected(self) -> None:
		self._connected = True

	async def on_disconnect(self) -> None:
		self._connected = False
		for key, redo_data_dict in self._redo_data_map.items():
			async with self.get_lock_for_class(key):
				for redo_data in redo_data_dict.values():
					redo_data.set_registered(False)

	async def _execute_redo_task(self):
		while not self._stop_event.is_set():
			try:
				await asyncio.wait_for(self._execute_redo_channel.get(),
									   timeout=30)
			except asyncio.TimeoutError:
				self._logger.debug(" Execute redo task timeout occurred")
			except asyncio.CancelledError:
				return

			if not self._connected:
				self._logger.warning("Grpc Connection is disconnect, skip current redo task")
				return

			try:
				await self.redo_task()
			except Exception as e:
				self._logger.error("Execute redo task error, error message: %s", e)

	@abstractmethod
	async def redo_task(self):
		pass

	def get_lock_for_class(self, data_type: str) -> AsyncRLock:
		"""为特定类类型获取锁，如果不存在则创建"""
		if data_type not in self._locks:
			self._locks[data_type] = AsyncRLock()
		return self._locks[data_type]

	async def cached_redo_data(self, key: str, redo_data: RedoData,
			data_type: str) -> None:

		if data_type not in self._redo_data_map:
			self._redo_data_map[data_type] = {}

		actual_redo_data = self._redo_data_map[data_type]
		lock = self.get_lock_for_class(data_type)
		async with lock:
			actual_redo_data[key] = redo_data

	async def remove_redo_data(self, key: str, data_type: str) -> None:
		"""
		删除redo数据

		Args:
			key: redo数据的键
			data_type: 存储在RedoData中的数据类型
		"""
		if data_type not in self._redo_data_map:
			self._redo_data_map[data_type] = {}

		actual_redo_data = self._redo_data_map[data_type]
		lock = self.get_lock_for_class(data_type)
		async with lock:
			redo_data = actual_redo_data.get(key)
			if redo_data is not None and not redo_data.is_expected_registered():
				actual_redo_data.pop(key, None)

	async def data_registered(self, key: str, data_type: str) -> None:
		"""
		数据注册成功，标记注册状态为True

		Args:
			key: redo数据的键
			data_type: 存储在RedoData中的类类型
		"""
		if data_type not in self._redo_data_map:
			self._redo_data_map[data_type] = {}

		actual_redo_data = self._redo_data_map[data_type]
		lock = self.get_lock_for_class(data_type)
		async with lock:
			redo_data = actual_redo_data.get(key)
			if redo_data is not None:
				redo_data.registered()

	async def data_deregister(self, key: str, data_type:str) -> None:
		"""
		数据注销，标记注销状态为True

		Args:
			key: redo数据的键
			data_type: 存储在RedoData中的类类型
		"""
		if data_type not in self._redo_data_map:
			self._redo_data_map[data_type] = {}

		actual_redo_data = self._redo_data_map[data_type]
		lock = self.get_lock_for_class(data_type)
		async with lock:
			redo_data = actual_redo_data.get(key)
			if redo_data is not None:
				redo_data.set_unregistering(True)
				redo_data.set_expected_registered(False)

	async def data_deregistered(self, key: str, data_type: str) -> None:
		"""
		数据注销完成，标记注销状态

		Args:
			key: redo数据的键
			data_type: 存储在RedoData中的类类型
		"""
		if data_type not in self._redo_data_map:
			self._redo_data_map[data_type] = {}

		actual_redo_data = self._redo_data_map[data_type]
		lock = self.get_lock_for_class(data_type)
		async with lock:
			redo_data = actual_redo_data.get(key)
			if redo_data is not None:
				redo_data.unregistered()

	async def is_data_registered(self, key: str, data_type: str) -> bool:
		"""
		判断数据是否已注册到服务器

		Args:
			key: redo数据的键
			data_type: 存储在RedoData中的类类型

		Returns:
			bool: 如果已注册返回True，否则返回False
		"""
		if data_type not in self._redo_data_map:
			self._redo_data_map[data_type] = {}

		actual_redo_data = self._redo_data_map[data_type]
		lock = self.get_lock_for_class(data_type)
		async with lock:
			redo_data = actual_redo_data.get(key)
			return redo_data is not None and redo_data.is_registered()

	async def find_redo_data(self, data_type: str) -> Set[RedoData]:
		"""
		查找所有需要redo的数据

		Args:
			data_type: 存储在RedoData中的类类型

		Returns:
			Set[RedoData]: 需要redo的数据集合
		"""
		result: Set[RedoData] = set()
		if data_type not in self._redo_data_map:
			self._redo_data_map[data_type] = {}

		actual_redo_data = self._redo_data_map[data_type]
		lock = self.get_lock_for_class(data_type)
		async with lock:
			for redo_data in actual_redo_data.values():
				if redo_data.is_need_redo():
					result.add(redo_data)

		return result

	async def get_redo_data(self, key: str, data_type: str) -> Optional[RedoData]:
		"""
		获取缓存的redo数据

		Args:
			key: redo数据的键
			data_type: 存储在RedoData中的类类型

		Returns:
			RedoData: 缓存的redo数据
		"""
		if data_type not in self._redo_data_map:
			self._redo_data_map[data_type] = {}

		actual_redo_data = self._redo_data_map[data_type]
		lock = self.get_lock_for_class(data_type)
		async with lock:
			return actual_redo_data.get(key)


	async def start_redo_task(self):
		await self._execute_redo_channel.put(None)

	async def close_client(self):
		self._logger.info(f"{self._module} close redo service ...")
		self._stop_event.set()
		await self._listen_task
		self._redo_data_map.clear()
		self._locks.clear()



