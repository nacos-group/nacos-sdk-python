from typing import Optional, Any

from v2.nacos.naming.model.service import Service
from v2.nacos.transport.model.rpc_response import Response


class NotifySubscriberResponse(Response):
    def get_response_type(self) -> str:
        return "NotifySubscriberResponse"


class SubscribeServiceResponse(Response):
    serviceInfo: Optional[Service] = None

    def get_response_type(self) -> str:
        return "SubscribeServiceResponse"

    def get_service_info(self) -> Service:
        return self.serviceInfo


class InstanceResponse(Response):
    def get_response_type(self) -> str:
        return "InstanceResponse"


class BatchInstanceResponse(Response):
    def get_response_type(self) -> str:
        return "BatchInstanceResponse"


class ServiceListResponse(Response):
    count: int
    serviceNames: list[str]

    def get_response_type(self) -> str:
        return "ServiceListResponse"
