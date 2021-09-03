from typing import Optional

from v2.nacos.remote.requests.abstract_naming_request import AbstractNamingRequest
from v2.nacos.remote.utils import remote_request_type


class ServiceQueryRequest(AbstractNamingRequest):
    cluster: Optional[str]
    healthyOnly: Optional[bool]
    udpPort: Optional[int]

    def get_cluster(self) -> str:
        return self.cluster

    def set_cluster(self, cluster: str) -> None:
        self.cluster = cluster

    def is_healthy_only(self) -> bool:
        return self.healthyOnly

    def set_healthy_only(self, healthy_only: bool) -> None:
        self.healthyOnly = healthy_only

    def get_udp_port(self) -> int:
        return self.udpPort

    def set_udp_port(self, udp_port: int) -> None:
        self.udpPort = udp_port

    def get_remote_type(self) -> str:
        return remote_request_type["NamingServiceQuery"]
