from typing import Optional

from v2.nacos.remote.requests.abstract_naming_request import AbstractNamingRequest
from v2.nacos.remote.utils import remote_request_type


class SubscribeServiceRequest(AbstractNamingRequest):
    subscribe: Optional[bool]
    clusters: Optional[str]

    def get_remote_type(self) -> str:
        return remote_request_type["NamingSubscribeService"]

    def get_clusters(self) -> str:
        return self.clusters

    def set_clusters(self, clusters: str) -> None:
        self.clusters = clusters

    def is_subscribe(self) -> bool:
        return self.subscribe

    def set_subscribe(self, subscribe: bool) -> None:
        self.subscribe = subscribe
