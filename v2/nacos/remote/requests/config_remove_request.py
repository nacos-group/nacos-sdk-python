from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class ConfigRemoveRequest(request.Request):
    def __init__(self):
        super().__init__()
        self.__MODULE = "config"
        self.__data_id = ""
        self.__group = ""
        self.__tenant = ""
        self.__tag = ""

    def get_module(self):
        return self.__MODULE

    def get_remote_type(self):
        return remote_request_type["ConfigRemove"]

    def get_data_id(self) -> str:
        return self.__data_id

    def set_data_id(self, data_id: str) -> None:
        self.__data_id = data_id

    def get_group(self) -> str:
        return self.__group

    def set_group(self, group: str) -> None:
        self.__group = group

    def get_tenant(self) -> str:
        return self.__tenant

    def set_tenant(self, tenant: str) -> None:
        self.__tenant = tenant

    def get_tag(self) -> str:
        return self.__tag

    def set_tag(self, tag: str) -> None:
        self.__tag = tag
