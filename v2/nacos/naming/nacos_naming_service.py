import logging
from typing import List

from v2.nacos.naming.cache.service_info_holder import ServiceInfoHolder
from v2.nacos.naming.core.balancer import Balancer
from v2.nacos.naming.dtos.instance import Instance
from v2.nacos.naming.event.instances_change_notifier import InstancesChangeNotifier
from v2.nacos.naming.ievent_listener import EventListener
from v2.nacos.naming.remote.naming_client_proxy_delegate import NamingClientProxyDelegate
from v2.nacos.naming.utils.naming_utils import NamingUtils


class NacosNamingService:
    UP = "UP"

    DOWN = "DOWN"

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
        instance = Instance(ip=ip, port=port, weight=1.0, cluster_name=cluster_name, service_name=service_name)
        NamingUtils.check_instance_is_legal(instance)
        self.client_proxy.register_service(service_name, group_name, instance)

    def deregister_instance(self, service_name: str, group_name: str, ip: str, port: int, cluster_name: str) -> None:
        instance = Instance(ip=ip, port=port, cluster_name=cluster_name, service_name=service_name)
        self.client_proxy.deregister_service(service_name, group_name, instance)

    def get_all_instances(self, service_name: str, group_name: str, clusters: List[str], subscribe: bool) -> List[Instance]:
        cluster_string = ",".join(clusters)
        if subscribe:
            service_info = self.service_info_holder.get_service_info(service_name, group_name, cluster_string)
        else:
            service_info = self.client_proxy.query_instances_of_service(
                service_name, group_name, cluster_string, 0, False
            )
        if not service_info or not service_info.get_hosts():
            return []

        return service_info.get_hosts()

    def select_instances(self, service_name: str, group_name: str, clusters: List[str], healthy: bool, subscribe: bool) -> List[Instance]:
        cluster_string = ",".join(clusters)
        if subscribe:
            service_info = self.service_info_holder.get_service_info(service_name, group_name, cluster_string)
            if not service_info:
                service_info = self.client_proxy.subscribe(service_name, group_name, cluster_string)
        else:
            service_info = self.client_proxy.query_instances_of_service(
                service_name, group_name, cluster_string, 0, False
            )

        if not service_info or not service_info.get_hosts():
            return []

        instances_list = service_info.get_hosts()
        for instance in instances_list:
            if healthy != instance.is_healthy() or not instance.is_enabled() or instance.get_weight() <= 0:
                instances_list.remove(instance)

        service_info.set_hosts(instances_list)
        return instances_list

    def select_one_healthy_instance(self, service_name: str, group_name: str, clusters: List[str], subscribe: bool) -> Instance:
        cluster_string = ",".join(clusters)
        if subscribe:
            service_info = self.service_info_holder.get_service_info(service_name, group_name, cluster_string)
            if not service_info:
                service_info = self.client_proxy.subscribe(service_name, group_name, cluster_string)
            return Balancer.RandomByWeight.select_host(service_info)
        else:
            service_info = self.client_proxy.query_instances_of_service(
                service_name, group_name, cluster_string, 0, False
            )
            return Balancer.RandomByWeight.select_host(service_info)

    def subscribe(self, service_name: str, group_name: str, clusters: List[str], listener: EventListener) -> None:
        if not listener:
            return

        cluster_string = ",".join(clusters)
        self.change_notifier.register_listener(group_name, service_name, cluster_string, listener)
        self.client_proxy.subscribe(service_name, group_name, cluster_string)

    def unsubscribe(self, service_name: str, group_name: str, clusters: List[str], listener: EventListener) -> None:
        cluster_string = ",".join(clusters)
        self.change_notifier.deregister_listener(group_name, service_name, cluster_string, listener)

        if not self.change_notifier.is_subscribed(group_name, service_name, cluster_string):
            self.client_proxy.unsubscribe(service_name, group_name, cluster_string)

    def get_services_of_server(self, page_no: int, page_size: int, group_name: str, selector):
        return self.client_proxy.get_service_list(page_no, page_size, group_name, selector)

    def get_server_status(self) -> str:
        return NacosNamingService.UP if self.client_proxy.server_healthy() else NacosNamingService.DOWN

    def shutdown(self) -> None:
        self.service_info_holder.shutdown()
        self.client_proxy.shutdown()
