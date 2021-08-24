from v2.nacos.remote.requests.abstract_naming_request import AbstractNamingRequest
from v2.nacos.remote.utils import remote_request_type


class SubscribeServiceRequest(AbstractNamingRequest):
    def __init__(self, namespace: str, group_name: str, service_name: str, clusters: str, subscribe: bool):
        super().__init__(namespace, service_name, group_name)
        self.clusters = clusters
        self.subscribe = subscribe

    def get_remote_type(self) -> str:
        return remote_request_type["NamingSubscribeService"]

    def get_clusters(self) -> str:
        return self.clusters

    def is_subscribe(self) -> bool:
        return self.subscribe
