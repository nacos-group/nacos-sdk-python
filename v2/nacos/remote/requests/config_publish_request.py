from typing import Dict
from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class ConfigPublishRequest(request.Request):
    def __init__(self, data_id=None, group=None, tenant=None, content=None):
        super().__init__()
        self.__MODULE = "config"
        self.data_id = data_id
        self.group = group
        self.tenant = tenant
        self.content = content
        self.cas_md5 = ""
        self.addition_map = {}

    def get_module(self):
        return self.__MODULE

    def get_remote_type(self):
        return remote_request_type["ConfigPublish"]

    def get_addition_param(self, key: str) -> str:
        return self.addition_map.get(key)

    def put_addition_param(self, key: str, value: str) -> str:
        self.addition_map[key] = value

    def get_data_id(self) -> str:
        return self.data_id

    def set_data_id(self, data_id: str) -> None:
        self.data_id = data_id

    def get_group(self) -> str:
        return self.group

    def set_group(self, group: str) -> None:
        self.group = group

    def get_content(self) -> str:
        return self.content

    def set_content(self, content: str) -> None:
        self.content = content

    def get_cas_md5(self) -> str:
        return self.cas_md5

    def set_cas_md5(self, cas_md5: str) -> None:
        self.cas_md5 = cas_md5

    def get_addition_map(self) -> Dict[str, str]:
        return self.addition_map

    def set_addition_map(self, addition_map: Dict[str, str]) -> None:
        self.addition_map = addition_map

    def get_tenant(self) -> str:
        return self.tenant

    def set_tenant(self, tenant: str) -> None:
        self.tenant = tenant
