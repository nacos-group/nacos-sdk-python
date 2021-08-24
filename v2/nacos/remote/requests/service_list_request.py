from v2.nacos.remote.requests.abstract_naming_request import AbstractNamingRequest
from v2.nacos.remote.utils import remote_request_type


class ServiceListRequest(AbstractNamingRequest):
    def __init__(self, namespace: str, group_name: str, page_no: int, page_size: int, service_name: str, selector: str):
        super().__init__(namespace, service_name, group_name)
        self.page_no = page_no
        self.page_size = page_size
        self.selector = selector

    def get_remote_type(self) -> str:
        return remote_request_type["NamingServiceList"]

    def get_page_no(self) -> int:
        return self.page_no

    def get_page_size(self) -> int:
        return self.page_size

    def get_selector(self) -> str:
        return self.selector
