import logging
from typing import List

from v2.nacos.naming.cache.service_info_holder import ServiceInfoHolder
from v2.nacos.naming.dtos.instance import Instance
from v2.nacos.naming.event.instances_change_notifier import InstancesChangeNotifier
from v2.nacos.naming.remote.naming_client_proxy_delegate import NamingClientProxyDelegate
from v2.nacos.naming.utils.naming_utils import NamingUtils


class NacosNamingService:
    def __init__(self, properties: dict):
        logging.basicConfig()
        self.logger = logging.getLogger(__name__)

        self.namespace = properties["namespace"]
        self.change_notifier = InstancesChangeNotifier()
        self.service_info_holder = ServiceInfoHolder(self.namespace, properties)
        self.client_proxy = NamingClientProxyDelegate(
            self.namespace, self.service_info_holder, properties, self.change_notifier
        )

    def register_instance(self, service_name: str, group_name: str, ip: str, port: int, cluster_name: str) -> None:
        instance = Instance(ip=ip, port=port, weight=1.0, cluster_name=cluster_name)
        NamingUtils.check_instance_is_legal(instance)
        self.client_proxy.register_service(service_name, group_name, instance)

    def deregister_instance(self, service_name: str, gourp_name: str, ip: str, port: int, cluster_name: str) -> None:
        pass

    def get_all_instances(self, service_name: str, group_name: str, clusters: List[str], subscribe: bool) -> List[Instance]:
        pass

    def select_instances(self, service_name: str, group_name: str, clusters: List[str], healthy: bool, subscribe: bool) -> List[Instance]:
        pass

    def select_one_healthy_instance(self, service_name: str, group_name: str, clusters: List[str], subscribe: bool) -> Instance:
        pass

    def subscribe(self, service_name: str, group_name: str, clusters: List[str], listener: EventListener) -> None:
        pass

    def unsubscribe(self, service_name: str, group_name: str, clusters: List[str], listener: EventListener) -> None:
        pass

    def get_services_of_server(self):
        pass

    def get_server_status(self) -> str:
        pass

    def shutdown(self) -> None:
        pass



