from v2.nacos.naming.dtos.service_info import ServiceInfo
from v2.nacos.remote.responses import response
from v2.nacos.remote.utils import remote_response_type


class QueryServiceResponse(response.Response):
    def __init__(self, service_info: ServiceInfo):
        super().__init__()
        self.service_info = service_info

    def get_remote_type(self):
        return remote_response_type["QueryService"]

    def get_service_info(self) -> ServiceInfo:
        return self.service_info
