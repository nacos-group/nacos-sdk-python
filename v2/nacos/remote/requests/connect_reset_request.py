from typing import Optional

from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class ConnectResetRequest(request.Request):
    serverIp: Optional[str]
    serverPort: Optional[str]

    def get_server_ip(self) -> str:
        return self.serverIp

    def set_server_ip(self, server_ip: str) -> None:
        self.serverIp = server_ip

    def get_server_port(self) -> str:
        return self.serverPort

    def set_server_port(self, sever_port: str) -> None:
        self.serverPort = sever_port

    def get_module(self):
        return "internal"

    def get_remote_type(self):
        return remote_request_type["ConnectReset"]
