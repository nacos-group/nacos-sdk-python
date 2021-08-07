from typing import Optional
from v2.nacos.remote.responses import response
from v2.nacos.remote.utils import remote_response_type
from v2.nacos.naming.dtos.service_info import ServiceInfo


class SubscribeServiceResponse(response.Response):
    def __init__(self, result_code:Optional[int]=None, message:Optional[str]=None,
                 service_info:Optional[ServiceInfo]=None):
        super().__init__()
        if result_code:
            self.set_result_code(result_code)
        if message:
            self.set_message(message)
        if service_info:
            self.__service_info = service_info

    def get_remote_type(self):
        return remote_response_type["SubscribeService"]

    def get_service_info(self) -> ServiceInfo:
        return self.__service_info

    def set_service_info(self, service_info: ServiceInfo) -> None:
        self.__service_info = service_info
