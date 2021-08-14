from abc import ABCMeta

from v2.nacos.remote.requests.request import Request


class AbstractNamingRequest(metaclass=ABCMeta, Request):
    def __init__(self, namespace: str, service_name: str, group_name: str):
        super().__init__()
        self.__MODULE = "naming"
        self.__namespace = namespace
        self.__service_name = service_name
        self.__group_name = group_name

    def get_module(self):
        return self.__MODULE

    def get_namespace(self) -> str:
        return self.__namespace

    def set_namespace(self, namespace: str) -> None:
        self.__namespace = namespace

    def get_service_name(self) -> str:
        return self.__service_name

    def set_service_name(self, service_name: str) -> None:
        self.__service_name = service_name

    def get_group_name(self) -> str:
        return self.__group_name

    def set_group_name(self, group_name: str) -> None:
        self.__group_name = group_name
