from typing import Optional, Any

from v2.nacos.naming.model.service_info import ServiceInfo
from v2.nacos.transport.model.rpc_response import Response


class NotifySubscriberResponse(Response):
    def get_response_type(self) -> str:
        return "NotifySubscriberResponse"


class SubscribeServiceResponse(Response):
    service_info: Optional[Any]

    def get_response_type(self) -> str:
        return "SubscribeServiceResponse"

    def get_service_info(self) -> ServiceInfo:
        return self.service_info


class InstanceResponse(Response):
    def get_response_type(self) -> str:
        return "InstanceResponse"
