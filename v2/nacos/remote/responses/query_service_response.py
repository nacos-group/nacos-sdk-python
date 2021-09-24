from typing import Optional, Any

from v2.nacos.naming.dtos.service_info import ServiceInfo
from v2.nacos.remote.responses import response
from v2.nacos.remote.utils import remote_response_type


class QueryServiceResponse(response.Response):
    serviceInfo: Optional[Any]

    def get_remote_type(self):
        return remote_response_type["QueryService"]

    def get_service_info(self) -> ServiceInfo:
        return self.serviceInfo

    pass
