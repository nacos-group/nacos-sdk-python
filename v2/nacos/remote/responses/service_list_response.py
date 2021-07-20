from typing import List
from v2.nacos.remote.responses import response
from v2.nacos.remote.utils import remote_response_type


class ServiceListResponse(response.Response):
    def __init__(self):
        super().__init__()
        self.count = 0
        self.service_name = []

    def get_remote_type(self):
        return remote_response_type["ServiceList"]

    def get_count(self) -> int:
        return self.count

    def set_count(self, count:int) -> None:
        self.count = count

    def get_service_name(self) -> List[str]:
        return self.service_name

    def set_service_name(self, service_name: List[str]) -> None:
        self.service_name = service_name