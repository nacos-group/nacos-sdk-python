from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.naming.dtos.instance import Instance
from v2.nacos.naming.dtos.service_info import ServiceInfo
from v2.nacos.naming.utils.naming_utils import NamingUtils
from v2.nacos.remote.iconnection_event_listener import ConnectionEventListener
import logging


class NamingGrpcConnectionEventListener(ConnectionEventListener):
    def __init__(self, client_proxy):
        logging.basicConfig()
        self.logger = logging.getLogger(__name__)

        self.client_proxy = client_proxy
        self.registered_instance_cached = {}
        self.subscribes = []

    def on_connected(self) -> None:
        self.__redo_subscribe()
        self.__redo_register_each_service()

    def on_disconnect(self) -> None:
        self.logger.info("Grpc connection disconnected")

    def __redo_subscribe(self) -> None:
        self.logger.info("Grpc reconnect, redo subscribe services")
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

    def __redo_register_each_service(self) -> None:
        self.logger.info("Grpc reconnect, redo register services")
        for key, value in self.registered_instance_cached.items():
            service_name = NamingUtils.get_service_name(key)
            group_name = NamingUtils.get_grouped_name(key)
            self.__redo_register_each_instance(service_name, group_name, value)

    def __redo_register_each_instance(self, service_name: str, group_name: str, instance: Instance) -> None:
        try:
            self.client_proxy.register_service(service_name, group_name, instance)
        except NacosException as e:
            self.logger.info("redo register for service %s@@%s, %s failed: %s"
                             % (group_name, service_name, str(instance), e))

    def cache_instance_for_redo(self, service_name: str, group_name: str, instance: Instance) -> None:
        key = NamingUtils.get_grouped_name(service_name, group_name)
        self.registered_instance_cached[key] = instance

    def remove_instance_for_redo(self, service_name: str, group_name: str, instance: Instance) -> None:
        key = NamingUtils.get_grouped_name(service_name, group_name)
        self.registered_instance_cached.pop(key)

    def cache_subscribe_for_redo(self, full_service_name: str, cluster: str) -> None:
        self.subscribes.append(ServiceInfo.get_key(full_service_name, cluster))

    def remove_subscriber_for_redo(self, full_service_name: str, cluster: str) -> None:
        self.subscribes.remove(ServiceInfo.get_key(full_service_name, cluster))
