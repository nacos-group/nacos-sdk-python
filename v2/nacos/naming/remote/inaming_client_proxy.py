from abc import ABCMeta, abstractmethod

from v2.nacos.common.lifecycle.closeable import Closeable


class NamingClientProxy(metaclass=ABCMeta, Closeable):
    @abstractmethod
    def register_service(self, service_name, group_name, instance):
        pass

    @abstractmethod
    def deregister_service(self, service_name, group_name, instance):
        pass

    @abstractmethod
    def update_instance(self, service_name, group_name, instance):
        pass

    @abstractmethod
    def query_instances_of_service(self, service_name, group_name, clusters, udp_port, healthy_only):
        pass

    @abstractmethod
    def query_service(self, service_name, group_name):
        pass

    @abstractmethod
    def create_service(self, service, selector):
        pass

    @abstractmethod
    def delete_service(self, service_name, group_name):
        pass

    @abstractmethod
    def update_service(self, service, selector):
        pass

    @abstractmethod
    def get_service_list(self, page_no, page_size, group_name, selector):
        pass

    @abstractmethod
    def subscribe(self, service_name, group_name, clusters):
        pass

    @abstractmethod
    def unsubscribe(self, modified_instances):
        pass

    @abstractmethod
    def server_healthy(self):
        pass

