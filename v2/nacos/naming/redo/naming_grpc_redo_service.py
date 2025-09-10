from typing import List, Set, cast

from v2.nacos import Instance
from v2.nacos.common.constants import Constants
from v2.nacos.naming.redo.naming_redo_data import NamingRedoData
from v2.nacos.naming.util.naming_client_util import get_group_name, \
	get_service_cache_key
from v2.nacos.redo.abstract_redo_service import AbstractRedoService
from v2.nacos.redo.redo_data import RedoData, RedoType

INSTANCE_REDO_DATA_TYPE = "InstanceRedoData"
SUBSCRIBE_REDO_DATA_TYPE = "SubscribeRedoData"


class NamingGrpcRedoService(AbstractRedoService):

	def __init__(self, client_proxy):
		super().__init__(Constants.NAMING_MODULE)
		from v2.nacos.naming.remote.naming_grpc_client_proxy import \
			NamingGRPCClientProxy
		if not isinstance(client_proxy, NamingGRPCClientProxy):
			raise TypeError(
					"client_proxy must be NamingGRPCClientProxy instance")
		self.proxy = client_proxy

	async def redo_task(self):
		await self.redo_for_instances()
		await self.redo_for_subscribes()

	async def redo_for_instances(self):
		for redo_data in await self.find_instance_redo_data():
			try:
				await self.redo_for_instance(redo_data)
			except Exception as e:
				self._logger.error(
						f"Redo instance operation {redo_data.get_redo_type()} for service:{redo_data.service_name} group:{redo_data.group_name} failed, error:{e}")

	async def redo_for_instance(self, instance_redo_data: NamingRedoData):
		redo_type = instance_redo_data.get_redo_type()
		self._logger.info(
				f"Redo instance operation {redo_type} for service:{instance_redo_data.service_name} group:{instance_redo_data.group_name}")
		if redo_type is RedoType.REGISTER:
			if not self.proxy.server_health():
				return
			await self.process_instance_register_redo_type(instance_redo_data)
		elif redo_type is RedoType.UNREGISTER:
			if not self.proxy.server_health():
				return
			await self.proxy.deregister_instance(
					instance_redo_data.service_name,
					instance_redo_data.group_name,
					instance_redo_data.get()
			)
		elif redo_type is RedoType.REMOVE:
			await self.remove_instance_for_redo(instance_redo_data.service_name,
												instance_redo_data.group_name)

	async def process_instance_register_redo_type(self,
			instance_redo_data: NamingRedoData):
		data = instance_redo_data.get()
		if isinstance(data, List):
			await self.proxy.batch_register_instance(
					instance_redo_data.service_name,
					instance_redo_data.group_name,
					data)
			return
		await self.proxy.register_instance(
				instance_redo_data.service_name,
				instance_redo_data.group_name,
				data
		)

	async def redo_for_subscribes(self):
		for redo_data in await self.find_subscribe_redo_data():
			try:
				await self.redo_for_subscribe(redo_data)
			except Exception as e:
				self._logger.error(
						f"Redo subscribe operation {redo_data.get_redo_type()} for service:{redo_data.service_name} group:{redo_data.group_name} failed, error:{e}")

	async def redo_for_subscribe(self, subscribe_redo_data: NamingRedoData):
		redo_type = subscribe_redo_data.get_redo_type()
		self._logger.info(
				f"Redo subscribe operation {redo_type} for service:{subscribe_redo_data.service_name} group:{subscribe_redo_data.group_name}")
		if redo_type is RedoType.REGISTER:
			if not self.proxy.server_health():
				return
			await self.proxy.subscribe(subscribe_redo_data.service_name,
									   subscribe_redo_data.group_name,
									   subscribe_redo_data.get())
		elif redo_type is RedoType.UNREGISTER:
			if not self.proxy.server_health():
				return
			await self.proxy.unsubscribe(
					subscribe_redo_data.service_name,
					subscribe_redo_data.group_name,
					subscribe_redo_data.get()
			)
		elif redo_type is RedoType.REMOVE:
			await self.remove_subscribe_for_redo(
				subscribe_redo_data.service_name,
				subscribe_redo_data.group_name, subscribe_redo_data.get())

	async def cache_instance_for_redo(self, service_name: str, group_name: str,
			instance: Instance) -> None:
		key = get_group_name(service_name, group_name)
		redo_data = NamingRedoData(
				data=instance,
				service_name=service_name,
				group_name=group_name,
		)
		await super().cached_redo_data(key, redo_data, INSTANCE_REDO_DATA_TYPE)

	async def cache_instances_for_redo(self, service_name: str, group_name: str,
			instances: List[Instance]) -> None:
		key = get_group_name(service_name, group_name)
		redo_data = NamingRedoData(
				data=instances,
				service_name=service_name,
				group_name=group_name,
		)
		await super().cached_redo_data(key, redo_data, INSTANCE_REDO_DATA_TYPE)

	async def instance_registered(self, service_name: str,
			group_name: str) -> None:
		key = get_group_name(service_name, group_name)
		await super().data_registered(key, INSTANCE_REDO_DATA_TYPE)

	async def instance_deregister(self, service_name: str,
			group_name: str) -> None:
		key = get_group_name(service_name, group_name)
		await super().data_deregister(key, INSTANCE_REDO_DATA_TYPE)

	async def instance_deregistered(self, service_name: str,
			group_name: str) -> None:
		key = get_group_name(service_name, group_name)
		await super().data_deregistered(key, INSTANCE_REDO_DATA_TYPE)

	async def remove_instance_for_redo(self, service_name: str,
			group_name: str) -> None:
		key = get_group_name(service_name, group_name)
		await super().remove_redo_data(key, INSTANCE_REDO_DATA_TYPE)

	async def find_instance_redo_data(self) -> Set[NamingRedoData]:
		redo_data_set = await super().find_redo_data(INSTANCE_REDO_DATA_TYPE)
		return cast(Set[NamingRedoData], redo_data_set)

	async def find_instance_redo_data_by_service_key(self,
			service_name: str, group_name: str) -> NamingRedoData | None:
		service_key = get_group_name(service_name, group_name)
		redo_data = await super().get_redo_data(service_key,
												INSTANCE_REDO_DATA_TYPE)
		if isinstance(redo_data, NamingRedoData):
			return redo_data

	async def cache_subscribe_for_redo(self, service_name: str, group_name: str,
			cluster: str):
		service_key = get_group_name(service_name, group_name)
		key = get_service_cache_key(service_key, cluster)
		redo_data = NamingRedoData(
				data=cluster,
				service_name=service_name,
				group_name=group_name,
		)
		await super().cached_redo_data(key, redo_data, SUBSCRIBE_REDO_DATA_TYPE)

	async def is_subscribe_registered(self, service_name: str, group_name: str,
			cluster: str):
		service_key = get_group_name(service_name, group_name)
		key = get_service_cache_key(service_key, cluster)
		return await super().is_data_registered(key, SUBSCRIBE_REDO_DATA_TYPE)

	async def subscribe_registered(self, service_name: str, group_name: str,
			cluster: str) -> None:
		service_key = get_group_name(service_name, group_name)
		key = get_service_cache_key(service_key, cluster)
		await super().data_registered(key, SUBSCRIBE_REDO_DATA_TYPE)

	async def subscribe_deregister(self, service_name: str, group_name: str,
			cluster: str) -> None:
		service_key = get_group_name(service_name, group_name)
		key = get_service_cache_key(service_key, cluster)
		await super().data_deregister(key, SUBSCRIBE_REDO_DATA_TYPE)

	async def subscribe_deregistered(self, service_name: str, group_name: str,
			cluster: str) -> None:
		service_key = get_group_name(service_name, group_name)
		key = get_service_cache_key(service_key, cluster)
		await super().data_deregistered(key, SUBSCRIBE_REDO_DATA_TYPE)

	async def remove_subscribe_for_redo(self, service_name: str,
			group_name: str, cluster: str) -> None:
		service_key = get_group_name(service_name, group_name)
		key = get_service_cache_key(service_key, cluster)
		await super().remove_redo_data(key, SUBSCRIBE_REDO_DATA_TYPE)

	async def find_subscribe_redo_data(self) -> Set[NamingRedoData]:
		redo_data_set = await super().find_redo_data(SUBSCRIBE_REDO_DATA_TYPE)
		return cast(Set[NamingRedoData], redo_data_set)
