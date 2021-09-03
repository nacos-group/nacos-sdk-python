from abc import ABCMeta
from typing import Optional

from v2.nacos.remote.requests.request import Request


class AbstractNamingRequest(Request, metaclass=ABCMeta):
    namespace: Optional[str]
    serviceName: Optional[str]
    groupName: Optional[str]

    def get_module(self):
        return "naming"

    def get_namespace(self) -> str:
        return self.namespace

    def set_namespace(self, namespace: str) -> None:
        self.namespace = namespace

    def get_service_name(self) -> str:
        return self.serviceName

    def set_service_name(self, service_name: str) -> None:
        self.serviceName = service_name

    def get_group_name(self) -> str:
        return self.groupName

    def set_group_name(self, group_name: str) -> None:
        self.groupName = group_name
