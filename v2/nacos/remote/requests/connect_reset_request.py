from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class ConnectResetRequest(request.Request):
    def __init__(self):
        super().__init__()
        self.__MODULE = "internal"
        self.__server_ip = ""
        self.__server_port = ""

    def get_server_ip(self) -> str:
        return self.__server_ip

    def set_server_ip(self, server_ip: str) -> None:
        self.__server_ip = server_ip

    def get_server_port(self) -> str:
        return self.__server_port

    def set_server_port(self, sever_port: str) -> None:
        self.__server_port = sever_port

    def get_module(self):
        return self.__MODULE

    def get_remote_type(self):
        return remote_request_type["ConnectReset"]
