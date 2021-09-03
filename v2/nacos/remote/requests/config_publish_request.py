from typing import Optional
from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class ConfigPublishRequest(request.Request):
    dataId: Optional[str]
    group: Optional[str]
    tenant: Optional[str]
    content: Optional[str]
    casMd5: Optional[str]
    additionMap: dict = {}

    def get_module(self):
        return "config"

    def get_remote_type(self):
        return remote_request_type["ConfigPublish"]

    def get_addition_param(self, key: str) -> str:
        return self.additionMap.get(key)

    def put_addition_param(self, key: str, value: str) -> str:
        self.additionMap[key] = value

    def get_data_id(self) -> str:
        return self.dataId

    def set_data_id(self, data_id: str) -> None:
        self.dataId = data_id

    def get_group(self) -> str:
        return self.group

    def set_group(self, group: str) -> None:
        self.group = group

    def get_content(self) -> str:
        return self.content

    def set_content(self, content: str) -> None:
        self.content = content

    def get_cas_md5(self) -> str:
        return self.casMd5

    def set_cas_md5(self, cas_md5: str) -> None:
        self.casMd5 = cas_md5

    def get_addition_map(self) -> dict:
        return self.additionMap

    def set_addition_map(self, addition_map: dict) -> None:
        self.additionMap = addition_map

    def get_tenant(self) -> str:
        return self.tenant

    def set_tenant(self, tenant: str) -> None:
        self.tenant = tenant
