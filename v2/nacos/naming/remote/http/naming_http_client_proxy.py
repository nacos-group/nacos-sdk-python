import logging

from v2.nacos.naming.dtos.abstract_selector import AbstractSelector
from v2.nacos.naming.dtos.instance import Instance
from v2.nacos.naming.dtos.service import Service
from v2.nacos.naming.dtos.service_info import ServiceInfo
from v2.nacos.naming.remote.inaming_client_proxy import NamingClientProxy
from v2.nacos.remote.list_view import ListView


class NamingHttpClientProxy(NamingClientProxy):
    DEFAULT_SERVER_PORT = 8848

    def __init__(self, logger, namespace_id=None,
                 security_proxy=None,
                 server_list_manager=None,
                 properties=None,
                 service_info_holder=None):
        self.logger = logger

        self.server_list_manager = server_list_manager
        self.server_port = NamingHttpClientProxy.DEFAULT_SERVER_PORT
        self.namespace_id = namespace_id

    def register_service(self, service_name: str, group_name: str, instance: Instance) -> None:
        pass

    def deregister_service(self, service_name: str, group_name: str, instance: Instance) -> None:
        pass

    def update_instance(self, service_name: str, group_name: str, instance: Instance) -> None:
        pass

    def query_instances_of_service(self, service_name: str, group_name: str, clusters: str, udp_port: int,
                                   healthy_only: bool):
        pass

    def query_service(self, service_name: str, group_name: str) -> Service:
        pass

    def create_service(self, service: Service, selector: AbstractSelector) -> None:
        pass

    def delete_service(self, service_name: str, group_name: str) -> bool:
        pass

    def update_service(self, service: Service, selector: AbstractSelector) -> None:
        pass

    def get_service_list(self, page_no: int, page_size: int, group_name: str, selector: AbstractSelector) -> ListView:
        pass

    def subscribe(self, service_name: str, group_name: str, clusters: str) -> ServiceInfo:
        pass

    def unsubscribe(self, service_name: str, group_name: str, clusters: str) -> None:
        pass

    def update_beat_info(self, modified_instances: list) -> None:
        pass

    def server_healthy(self) -> bool:
        pass

    def shutdown(self) -> None:
        pass
