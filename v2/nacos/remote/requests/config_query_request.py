from typing import Optional

from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class ConfigQueryRequest(request.Request):
    dataId: Optional[str]
    group: Optional[str]
    tenant: Optional[str]
    tag: Optional[str]

    NOTIFY_HEADER = "notify"

    def get_module(self) -> str:
        return "config"

    def get_remote_type(self):
        return remote_request_type["ConfigQuery"]

    def get_data_id(self) -> str:
        return self.dataId

    def set_data_id(self, data_id: str) -> None:
        self.dataId = data_id

    def get_group(self) -> str:
        return self.group

    def set_group(self, group: str) -> None:
        self.group = group

    def get_tenant(self) -> str:
        return self.tenant

    def set_tenant(self, tenant: str) -> None:
        self.tenant = tenant

    def get_tag(self) -> str:
        return self.tag

    def set_tag(self, tag: str) -> None:
        self.tag = tag

    def is_notify(self) -> bool:
        notify = self.get_header(ConfigQueryRequest.NOTIFY_HEADER, str(False))
        return bool(notify)

    @staticmethod
    def build(data_id: str, group: str, tenant: str):
        new_request = ConfigQueryRequest()
        new_request.set_data_id(data_id)
        new_request.set_group(group)
        new_request.set_tenant(tenant)
        return new_request
