from abc import ABC, abstractmethod
from v2.nacos.naming.model.instance import Instance


class NamingClientProxy(ABC):

    @abstractmethod
    def register_instance(self, service_name: str, group_name: str, instance: Instance) -> bool:
        pass

    @abstractmethod
    def batch_register_instance(self, service_name: str, group_name: str, instances: list):
        pass

    @abstractmethod
    def deregister_instance(self, service_name: str, group_name: str, instance: Instance):
        pass

    @abstractmethod
    def get_service_list(self, page_no, page_size, group_name, namespace_id, selector):
        pass

    @abstractmethod
    def server_healthy(self):
        pass

    @abstractmethod
    def query_instances_of_service(self, service_name, group_name, clusters, udp_port, healthy_only):
        pass

    @abstractmethod
    def subscribe(self, service_name, group_name, clusters):
        pass

    @abstractmethod
    def unsubscribe(self, modified_instances):
        pass

    @abstractmethod
    def close_client(self):
        pass
