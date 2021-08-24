from v2.nacos.remote.requests.abstract_naming_request import AbstractNamingRequest
from v2.nacos.remote.utils import remote_request_type


class ServiceQueryRequest(AbstractNamingRequest):
    def __init__(self, namespace: str, service_name: str, group_name: str,
                 cluster=None, healthy_only=None, udp_port=None):
        super().__init__(namespace, service_name, group_name)
        self.cluster = cluster  # str
        self.healthy_only = healthy_only  # bool
        self.udp_port = udp_port  # int

    def get_cluster(self) -> str:
        return self.cluster

    def is_healthy_only(self) -> bool:
        return self.healthy_only

    def get_udp_port(self) -> int:
        return self.udp_port

    def get_remote_type(self) -> str:
        return remote_request_type["NamingServiceQuery"]
