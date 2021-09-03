from typing import Optional
from v2.nacos.remote.responses import response
from v2.nacos.remote.utils import remote_response_type


class ServiceListResponse(response.Response):
    count: Optional[int]
    serviceNames: list = []

    def get_remote_type(self):
        return remote_response_type["ServiceList"]

    def get_count(self) -> int:
        return self.count

    def set_count(self, count: int) -> None:
        self.count = count

    def get_service_names(self) -> list:
        return self.serviceNames

    def set_service_names(self, service_names: list) -> None:
        self.serviceNames = service_names
