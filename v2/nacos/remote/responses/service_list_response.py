from typing import List
from v2.nacos.remote.responses import response
from v2.nacos.remote.utils import remote_response_type


class ServiceListResponse(response.Response):
    def __init__(self):
        super().__init__()
        self.count = 0
        self.service_names = []

    def get_remote_type(self):
        return remote_response_type["ServiceList"]

    def get_count(self) -> int:
        return self.count

    def set_count(self, count: int) -> None:
        self.count = count

    def get_service_names(self) -> List[str]:
        return self.service_names

    def set_service_names(self, service_names: List[str]) -> None:
        self.service_names = service_names
