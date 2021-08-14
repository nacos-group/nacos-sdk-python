from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class ConfigChangeNotifyRequest(request.Request):
    def __init__(self):
        super().__init__()
        self.__MODULE = "config"
        self.data_id = ""
        self.group = ""
        self.tenant = ""

    def get_module(self):
        return self.__MODULE

    def get_remote_type(self):
        return remote_request_type["ConfigChangeNotify"]

    def get_data_id(self) -> str:
        return self.data_id

    def set_data_id(self, data_id: str) -> None:
        self.data_id = data_id

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
        new_request = ConfigChangeNotifyRequest()
        new_request.set_data_id(data_id)
        new_request.set_group(group)
        new_request.set_tenant(tenant)
        return new_request
