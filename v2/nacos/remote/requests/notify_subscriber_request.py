from typing import Optional, Any

from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type
from v2.nacos.naming.dtos.service_info import ServiceInfo


class NotifySubscriberRequest(request.Request):
    namespace: Optional[str]
    serviceName: Optional[str]
    groupName: Optional[str]
    serviceInfo: Optional[Any]

    def get_module(self):
        return "naming"

    def get_remote_type(self):
        return remote_request_type["NamingNotifySubscriber"]

    def get_namespace(self) -> str:
        return self.namespace

    def set_namespace(self, namespace: str) -> None:
        self.namespace = namespace

    def get_service_name(self) -> str:
        return self.serviceName

    def set_service_name(self, service_name: str) -> None:
        self.serviceName = service_name

    def get_group_name(self) -> None:
        return self.groupName

    def set_group_name(self, group_name: str) -> None:
        self.groupName = group_name

    def get_service_info(self) -> ServiceInfo:
        return self.serviceInfo

    def set_service_info(self, service_info: ServiceInfo) -> None:
        self.serviceInfo = service_info

    @staticmethod
    def build_success_request(service_info: ServiceInfo):
        return NotifySubscriberRequest(serviceInfo=service_info)

    @staticmethod
    def build_fail_request(message: str):
        return NotifySubscriberRequest()
