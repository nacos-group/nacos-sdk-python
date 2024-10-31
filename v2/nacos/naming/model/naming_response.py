from typing import Optional, Any

from v2.nacos.naming.model.service_info import ServiceInfo
from v2.nacos.transport.model.rpc_response import Response


class NotifySubscriberResponse(Response):
    def get_response_type(self) -> str:
        return "NotifySubscriberResponse"


class SubscribeServiceResponse(Response):
    serviceInfo: ServiceInfo

    def get_response_type(self) -> str:
        return "SubscribeServiceResponse"

    def get_service_info(self) -> ServiceInfo:
        return self.service_info

class InstanceResponse(Response):
    def get_response_type(self) -> str:
        return "InstanceResponse"

class ServiceListResponse(Response):
    count: int
    serviceNames: list[str]

    def get_response_type(self) -> str:
        return "ServiceListResponse"
