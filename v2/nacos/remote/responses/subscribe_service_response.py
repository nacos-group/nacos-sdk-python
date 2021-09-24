from typing import Optional, Any
from v2.nacos.remote.responses import response
from v2.nacos.remote.utils import remote_response_type
from v2.nacos.naming.dtos.service_info import ServiceInfo


class SubscribeServiceResponse(response.Response):
    serviceInfo: Optional[Any]

    def get_remote_type(self):
        return remote_response_type["SubscribeService"]

    def get_service_info(self) -> ServiceInfo:
        return self.serviceInfo

    def set_service_info(self, service_info: ServiceInfo) -> None:
        self.serviceInfo = service_info
