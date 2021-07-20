from typing import Optional

from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type
from v2.nacos.naming.pojo.service_info import ServiceInfo

class NotifySubscriberRequest(request.Request):
    def __init__(self, service_info=None, message=None):
        super().__init__()
        self.__MODULE = "naming"
        self.__namespace = ""
        self.__service_name = ""
        self.__group_name = ""
        self.__service_info = service_info

    def get_module(self):
        return self.__MODULE

    def get_remote_type(self):
        return remote_request_type["NamingNotifySubscriber"]

    def get_namespace(self) -> str:
        return self.__namespace

    def set_namespace(self, namespace: str) -> None:
        self.__namespace = namespace

    def get_service_name(self) -> str:
        return self.__service_name

    def set_service_name(self, service_name: str) -> None:
        self.__service_name = service_name

    def get_group_name(self) -> None:
        return self.__group_name

    def set_group_name(self, group_name: str) -> None:
        self.__group_name = group_name

    def get_service_info(self) -> ServiceInfo:
        return self.__service_info

    def set_service_info(self, service_info: ServiceInfo) -> None:
        self.__service_info = service_info

    @staticmethod
    def build_success_request(service_info: ServiceInfo):
        return NotifySubscriberRequest(service_info, "success")

    @staticmethod
    def build_fail_request(message: str):
        return NotifySubscriberRequest()
