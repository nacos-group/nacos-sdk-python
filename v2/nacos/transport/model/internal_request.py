from typing import Dict
from v2.nacos.common.model.request import Request

# ClientAbilities 结构体在 Go 中没有属性，因此在 Python 中可以省略
class ClientAbilities:
    pass

class InternalRequest(Request):
    def __init__(self):
        super().__init__()
        self.module = "internal"

    @staticmethod
    def new_internal_request():
        return InternalRequest()


class HealthCheckRequest(InternalRequest):
    def __init__(self):
        super().__init__() 

    @staticmethod
    def new_health_check_request():
        return HealthCheckRequest()

    def get_request_type(self):
        return "HealthCheckRequest"


class ConnectResetRequest(InternalRequest):
    def __init__(self, server_ip: str, server_port: str):
        super().__init__()
        self._server_ip = server_ip
        self._server_port = server_port

    def get_request_type(self) -> str:
        return "ConnectResetRequest"


class ClientDetectionRequest(InternalRequest):
    def __init__(self):
        super().__init__()

    def get_request_type(self) -> str:
        return "ClientDetectionRequest"


class ServerCheckRequest(InternalRequest):
    def __init__(self):
        super().__init__() 

    @staticmethod
    def new_server_check_request():
        return ServerCheckRequest()

    def get_request_type(self):
        return "ServerCheckRequest"


class ConnectionSetupRequest(InternalRequest):
    def __init__(self):
        super().__init__()  # 调用父类构造方法
        self.client_version = ""
        self.tenant = ""
        self.labels = {}
        self.client_abilities = ClientAbilities()

    @staticmethod
    def new_connection_setup_request():
        return ConnectionSetupRequest()

    def get_request_type(self):
        return "ConnectionSetupRequest"