import time
from typing import Dict, List
from .rpc_request import Request
from ..model.service import Instance, Service
class ClientAbilities:
    pass

# model 模块中的 Service 和 Instance 类也需要定义
# 这里只是示例，具体实现需要根据实际的 model 模块


class NamingRequest(Request):
    def __init__(self, namespace: str, service_name: str, group_name: str):
        super().__init__()
        self._namespace = namespace
        self._service_name = service_name
        self._group_name = group_name
        self._module = "naming"

    @staticmethod
    def new_naming_request(namespace: str, service_name: str, group_name: str) -> 'NamingRequest':
        # request = Request() #python里不需要这样
        return NamingRequest(
            namespace=namespace,
            service_name=service_name,
            group_name=group_name
        )

    def get_string_to_sign(self) -> str:
        data = str(int(time.time() * 1000))
        if self._service_name or self._group_name:
            data = f"{data}@@{self._group_name}@@{self._service_name}"
        return data

class InstanceRequest(NamingRequest):
    def __init__(self, namespace: str, service_name: str, group_name: str, type: str, instance: Instance):
        super().__init__(namespace, service_name, group_name)
        self._type = type
        self._instance = instance

    @staticmethod
    def new_instance_request(namespace: str, service_name: str, group_name: str, type: str, instance: Instance) -> 'InstanceRequest':
        # naming_request = NamingRequest.new_naming_request(namespace, service_name, group_name)
        return InstanceRequest(
            namespace=namespace,
            service_name=service_name,
            group_name=group_name,
            type=type,
            instance=instance
        )

    def get_request_type(self) -> str:
        return "InstanceRequest"

# 其他请求类型的类
class BatchInstanceRequest(NamingRequest):
    def __init__(self, type: str, instances: List[Instance], namespace: str, service_name: str, group_name: str):
        super().__init__(namespace, service_name, group_name)
        self.type = type
        self.instances = instances

    @staticmethod
    def new_batch_instance_request(type: str, instances: List[Instance], namespace: str, service_name: str, group_name: str) -> 'BatchInstanceRequest':
        return BatchInstanceRequest(
            type=type,
            instances=instances,
            namespace=namespace,
            service_name=service_name,
            group_name=group_name
        )

    def get_request_type(self) -> str:
        return "BatchInstanceRequest"

# NotifySubscriberRequest类定义
class NotifySubscriberRequest(NamingRequest):
    def __init__(self, service_info: Service, namespace: str, service_name: str, group_name: str):
        super().__init__(namespace, service_name, group_name)
        self.service_info = service_info

    def get_request_type(self) -> str:
        return "NotifySubscriberRequest"

# ServiceListRequest类定义
class ServiceListRequest(NamingRequest):
    def __init__(self, namespace, service_name, group_name, page_no, page_size, selector):
        super().__init__(namespace, service_name, group_name)
        self.page_no = page_no
        self.page_size = page_size
        self.selector = selector

    @staticmethod
    def new_service_list_request(namespace, service_name, group_name, page_no, page_size, selector):
        # naming_request = NamingRequest.new_naming_request(namespace, service_name, group_name)
        return ServiceListRequest(
            namespace=namespace,
            service_name=service_name,
            group_name=group_name,
            page_no=page_no,
            page_size=page_size,
            selector=selector
        )

    def get_request_type(self):
        return "ServiceListRequest"

class SubscribeServiceRequest(NamingRequest):
    def __init__(self, namespace, service_name, group_name, subscribe, clusters):
        super().__init__(namespace, service_name, group_name) 
        self.subscribe = subscribe
        self.clusters = clusters

    @staticmethod
    def new_subscribe_service_request(namespace, service_name, group_name, clusters, subscribe):
        # naming_request = NamingRequest.new_naming_request(namespace, service_name, group_name)
        return SubscribeServiceRequest(
            namespace=namespace,
            service_name=service_name,
            group_name=group_name,
            clusters=clusters,
            subscribe=subscribe
        )

    def get_request_type(self):
        return "SubscribeServiceRequest"

class ServiceQueryRequest(NamingRequest):
    def __init__(self, namespace, service_name, group_name, cluster, healthy_only, udp_port):
        super().__init__(namespace, service_name, group_name)
        self.cluster = cluster
        self.healthy_only = healthy_only
        self.udp_port = udp_port

    @staticmethod
    def new_service_query_request(namespace, service_name, group_name, cluster, healthy_only, udp_port):
        # naming_request = NamingRequest.new_naming_request(namespace, service_name, group_name)
        return ServiceQueryRequest(
            namespace=namespace,
            service_name=service_name,
            group_name=group_name,
            cluster=cluster,
            healthy_only=healthy_only,
            udp_port=udp_port
        )

    def get_request_type(self):
        return "ServiceQueryRequest"