from typing import Optional

from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class ConfigChangeNotifyRequest(request.Request):
    dataId: Optional[str]
    group: Optional[str]
    tenant: Optional[str]

    def get_module(self):
        return "config"

    def get_remote_type(self):
        return remote_request_type["ConfigChangeNotify"]

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

    @staticmethod
    def build(data_id: str, group: str, tenant: str):
        new_request = ConfigChangeNotifyRequest(dataId=data_id, group=group, tenant=tenant)
        return new_request
