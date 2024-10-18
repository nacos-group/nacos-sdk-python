import asyncio

from v2.nacos.common.nacos_exception import NacosException
from v2.nacos.naming.model.instance import Instance
from v2.nacos.naming.model.service_info import ServiceInfo
from v2.nacos.naming.util.naming_client_util import get_group_name, get_service_cache_key
from v2.nacos.transport.connection_event_listener import ConnectionEventListener


class NamingGrpcConnectionEventListener(ConnectionEventListener):
    def __init__(self, client_proxy):
        self.logger = client_proxy.logger
        self.client_proxy = client_proxy
        self.registered_instance_cached = {}
        self.subscribes = []
        self.lock = asyncio.Lock()

    async def on_connected(self) -> None:
        await self.__redo_subscribe()
        # self.__redo_register_each_service()

    async def on_disconnect(self) -> None:
        self.logger.info("Grpc connection disconnected")

    async def __redo_subscribe(self) -> None:
        for each in self.subscribes:
            service_info = ServiceInfo.from_key(each)
            try:
                self.client_proxy.subscribe(
                    service_info.get_name(), service_info.group_name, service_info.get_clusters()
                )
            except NacosException as e:
                self.logger.info("re subscribe server %s failed: %s"
                                 % (service_info.get_name(), e)
                                 )

    # def __redo_register_each_service(self) -> None:
    #     self.logger.info("Grpc reconnect, redo register services")
    #     for key, value in self.registered_instance_cached.items():
    #         service_name = NamingUtils.get_service_name(key)
    #         group_name = NamingUtils.get_group_name(key)
    #         self.__redo_register_each_instance(service_name, group_name, value)

    def __redo_register_each_instance(self, service_name: str, group_name: str, instance: Instance) -> None:
        try:
            self.client_proxy.register_service(service_name, group_name, instance)
        except NacosException as e:
            self.logger.info("redo register for service %s@@%s, %s failed: %s"
                             % (group_name, service_name, str(instance), e))

    def cache_instance_for_redo(self, service_name: str, group_name: str, instance: Instance) -> None:
        key = get_group_name(service_name, group_name)
        self.registered_instance_cached[key] = instance

    def remove_instance_for_redo(self, service_name: str, group_name: str, instance: Instance) -> None:
        key = get_group_name(service_name, group_name)
        self.registered_instance_cached.pop(key, None)

    async def cache_subscribe_for_redo(self, full_service_name: str, cluster: str) -> None:
        cache_key = get_service_cache_key(full_service_name, cluster)
        with self.lock:
            if cache_key not in self.subscribes:
                self.subscribes.append(cache_key)

    def remove_subscriber_for_redo(self, full_service_name: str, cluster: str) -> None:
        cache_key = get_service_cache_key(full_service_name, cluster)
        with self.lock:
            self.subscribes.remove(cache_key)
