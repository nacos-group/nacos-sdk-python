from typing import Optional

from v2.nacos.remote.requests.abstract_naming_request import AbstractNamingRequest
from v2.nacos.remote.utils import remote_request_type


class ServiceListRequest(AbstractNamingRequest):
    pageNo: Optional[int]
    pageSize: Optional[int]
    selector: Optional[str]

    def get_remote_type(self) -> str:
        return remote_request_type["NamingServiceList"]

    def get_page_no(self) -> int:
        return self.pageNo

    def set_page_no(self, page_no: int) -> None:
        self.pageNo = page_no

    def get_page_size(self) -> int:
        return self.pageSize

    def set_page_size(self, page_size: int) -> None:
        self.pageSize = page_size

    def get_selector(self) -> str:
        return self.selector

    def set_selector(self, selector: str) -> None:
        self.selector = selector
