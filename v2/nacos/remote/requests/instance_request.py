from typing import Optional

from v2.nacos.naming.dtos.instance import Instance
from v2.nacos.remote.requests.abstract_naming_request import AbstractNamingRequest
from v2.nacos.remote.utils import remote_request_type


class InstanceRequest(AbstractNamingRequest):
    type: Optional[str]
    instance: Optional[Instance]

    def get_remote_type(self):
        return remote_request_type["NamingInstance"]

    def set_type(self, service_type: str) -> None:
        self.type = service_type

    def get_type(self) -> str:
        return self.type

    def set_instance(self, instance: Instance) -> None:
        self.instance = instance

    def get_instance(self) -> Instance:
        return self.instance
