import asyncio

from v2.nacos.naming.model.instance import Instance
from v2.nacos.naming.model.service import Service
from v2.nacos.naming.util.naming_client_util import get_group_name, get_service_cache_key
from v2.nacos.transport.connection_event_listener import ConnectionEventListener


class NamingGrpcConnectionEventListener(ConnectionEventListener):
    def __init__(self, client_proxy):
        self.logger = client_proxy.logger
        self.client_proxy = client_proxy
        self.registered_instance_cached = {}
        self.subscribes = {}
        self.lock = asyncio.Lock()

    async def on_connected(self) -> None:
        await self.__redo_subscribe()
        await self.__redo_register_each_service()

    async def on_disconnect(self) -> None:
        self.logger.info("grpc connection disconnected")

    async def __redo_subscribe(self) -> None:
        for service_key in self.subscribes.keys():
            try:
                service = Service.from_key(service_key)
                service_info = await self.client_proxy.subscribe(service.name, service.groupName, service.clusters)
            except Exception as e:
                self.logger.warning("failed to redo subscribe service %s, caused by: %s", service_key, e)
                continue
            await self.client_proxy.service_info_cache.process_service(service_info)

    async def __redo_register_each_service(self) -> None:
        for key, instanceVal in self.registered_instance_cached.items():
            info = Service.from_key(key)
            try:
                if isinstance(instanceVal, Instance):
                    await self.client_proxy.register_instance(info.name, info.groupName, instanceVal)
                elif isinstance(instanceVal, list) and all(isinstance(x, Instance) for x in instanceVal):
                    await self.client_proxy.batch_register_instance(info.name, info.groupName, info)
            except Exception as e:
                self.logger.info("redo register service %s@@%s failed: %s"
                                 % (info.groupName, info.name, e))

    async def cache_instance_for_redo(self, service_name: str, group_name: str, instance: Instance) -> None:
        key = get_group_name(service_name, group_name)
        async with self.lock:
            self.registered_instance_cached[key] = instance

    async def cache_instances_for_redo(self, service_name: str, group_name: str, instances: list[Instance]) -> None:
        key = get_group_name(service_name, group_name)
        async with self.lock:
            self.registered_instance_cached[key] = instances

    async def remove_instance_for_redo(self, service_name: str, group_name: str) -> None:
        key = get_group_name(service_name, group_name)
        async with self.lock:
            self.registered_instance_cached.pop(key)

    async def cache_subscribe_for_redo(self, full_service_name: str, cluster: str) -> None:
        cache_key = get_service_cache_key(full_service_name, cluster)
        async with self.lock:
            if cache_key not in self.subscribes:
                self.subscribes[cache_key] = None

    async def remove_subscriber_for_redo(self, full_service_name: str, cluster: str) -> None:
        cache_key = get_service_cache_key(full_service_name, cluster)
        async with self.lock:
            self.subscribes.pop(cache_key)
