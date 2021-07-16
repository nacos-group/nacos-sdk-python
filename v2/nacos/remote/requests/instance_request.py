from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class InstanceRequest(request.Request):
    def __init__(self, namespace=None, service_name=None, group_name=None):
        super().__init__()
        self.__MODULE = "naming"
        self.__namespace = namespace
        self.__service_name = service_name
        self.__group_name = group_name

    def get_module(self):
        return self.__MODULE

    def get_remote_type(self):
        return remote_request_type["NamingInstance"]

    def get_namespace(self):
        return self.__namespace

    def set_namespace(self, namespace):
        self.__namespace = namespace

    def get_service_name(self):
        return self.__service_name

    def set_service_name(self, service_name):
        self.__service_name = service_name

    def get_group_name(self):
        return self.__group_name

    def set_group_name(self, group_name):
        self.__group_name = group_name
