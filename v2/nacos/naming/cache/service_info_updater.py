import asyncio
import logging

from v2.nacos.common.constants import Constants
from v2.nacos.naming.cache.service_info_cache import ServiceInfoCache
from v2.nacos.naming.util.naming_client_util import get_group_name
from v2.nacos.utils.common_util import get_current_time_millis


class ServiceInfoUpdater:
	def __init__(self, service_info_holder: ServiceInfoCache,
			update_thread_num: int, naming_proxy):
		self.logger = logging.getLogger(Constants.NAMING_MODULE)
		self.service_info_holder = service_info_holder
		self.update_thread_num = update_thread_num

		from v2.nacos.naming.remote.naming_grpc_client_proxy import \
			NamingGRPCClientProxy
		if not isinstance(naming_proxy, NamingGRPCClientProxy):
			raise TypeError(
					"client_proxy must be NamingGRPCClientProxy instance")
		self.naming_proxy = naming_proxy

		self.stop_event = asyncio.Event()
		self.semaphore = asyncio.Semaphore(update_thread_num)

	async def async_update_service(self):
		while not self.stop_event.is_set():
			try:
				# 创建任务列表
				tasks = []

				# 遍历所有服务
				for key, service in self.service_info_holder.service_info_map.items():
					# 获取上次更新时间
					if not await self.service_info_holder.is_subscribed(
							get_group_name(service.name,service.groupName),service.clusters):
						continue

					last_ref_time = self.service_info_holder.update_time_map.get(
						key, 0)
					# 检查是否需要更新
					if get_current_time_millis() - last_ref_time > service.cacheMillis:
						# 创建受限的任务（使用信号量控制并发）
						task = self._create_limited_task(
								self.update_service_now,
								service.name, service.groupName,
								service.clusters
						)
						tasks.append(task)

				# 并发执行所有需要更新的任务
				if tasks:
					await asyncio.gather(*tasks, return_exceptions=True)

				# 等待1秒或直到被取消
				try:
					await asyncio.wait_for(self.stop_event.wait(), timeout=1.0)
					break  # 如果事件被设置则退出循环
				except asyncio.TimeoutError:
					# 正常超时，继续下一轮循环
					continue

			except asyncio.CancelledError:
				self.logger.info("Service update task was cancelled")
				break
			except Exception as e:
				self.logger.error(f"Error in service update loop: {e}")
				await asyncio.sleep(1)  # 出错时也等待避免忙循环

	async def _create_limited_task(self, func, *args):
		"""创建受信号量限制的任务"""
		async with self.semaphore:
			return await func(*args)

	async def update_service_now(self, service_name: str, group_name: str,
			clusters: str):
		try:
			service = await self.naming_proxy.query_instance_of_service(
					service_name, group_name, clusters, False)
			# 处理服务信息
			await self.service_info_holder.process_service(service)

		except Exception as e:
			logging.error(
				f"QueryInstances error, serviceName:{service_name}, cluster:{clusters}, err:{e}")

	def stop(self):
		"""停止服务更新"""
		self.stop_event.set()