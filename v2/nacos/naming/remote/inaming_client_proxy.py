from abc import ABCMeta, abstractmethod

from v2.nacos.common.lifecycle.closeable import Closeable
from v2.nacos.naming.dtos.abstract_selector import AbstractSelector
from v2.nacos.naming.dtos.instance import Instance
from v2.nacos.naming.dtos.service import Service
from v2.nacos.naming.dtos.service_info import ServiceInfo
from v2.nacos.remote.list_view import ListView


class NamingClientProxy(Closeable, metaclass=ABCMeta):
    @abstractmethod
    def register_service(self, service_name: str, group_name: str, instance: Instance) -> None:
        pass

    @abstractmethod
    def deregister_service(self, service_name: str, group_name: str, instance: Instance) -> None:
        pass

    @abstractmethod
    def update_instance(self, service_name: str, group_name: str, instance: Instance) -> None:
        pass

    @abstractmethod
    def query_instances_of_service(
            self, service_name: str, group_name: str, clusters: str, udp_port: int, healthy_only: bool
    ):
        pass

    @abstractmethod
    def query_service(self, service_name: str, group_name: str) -> Service:
        pass

    @abstractmethod
    def create_service(self, service: Service, selector: AbstractSelector) -> None:
        pass

    @abstractmethod
    def delete_service(self, service_name: str, group_name: str) -> bool:
        pass

    @abstractmethod
    def update_service(self, service: Service, selector: AbstractSelector) -> None:
        pass

    @abstractmethod
    def get_service_list(self, page_no: int, page_size: int, group_name: str, selector: AbstractSelector) -> ListView:
        pass

    @abstractmethod
    def subscribe(self, service_name: str, group_name: str, clusters: str) -> ServiceInfo:
        pass

    @abstractmethod
    def unsubscribe(self, service_name: str, group_name: str, clusters: str) -> None:
        pass

    @abstractmethod
    def update_beat_info(self, modified_instances: list) -> None:
        pass

    @abstractmethod
    def server_healthy(self) -> bool:
        pass

