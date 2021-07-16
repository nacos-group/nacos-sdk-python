from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class ConfigQueryRequest(request.Request):
    NOTIFY_HEADER = "notify"

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
        return remote_request_type["ConfigQuery"]

    def get_data_id(self):
        return self.__data_id

    def set_data_id(self, data_id):
        self.__data_id = data_id

    def get_group(self):
        return self.__group

    def set_group(self, group):
        self.__group = group

    def get_tenant(self):
        return self.__tenant

    def set_tenant(self, tenant):
        self.__tenant = tenant

    def get_tag(self):
        return self.__tag

    def set_tag(self, tag):
        self.__tag = tag

    def is_notify(self):
        notify = self.get_header(ConfigQueryRequest.NOTIFY_HEADER, str(False))
        return bool(notify)

    @staticmethod
    def build(data_id, group, tenant):
        new_request = ConfigQueryRequest()
        new_request.set_data_id(data_id)
        new_request.set_group(group)
        new_request.set_tenant(tenant)
        return new_request
