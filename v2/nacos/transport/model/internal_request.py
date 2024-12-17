from abc import ABC
from typing import Optional

from v2.nacos.transport.model.rpc_request import Request

CONNECTION_RESET_REQUEST_TYPE = "ConnectResetRequest"
CLIENT_DETECTION_REQUEST_TYPE = "ClientDetectionRequest"


class InternalRequest(Request, ABC):
    def __init__(self):
        super().__init__()

    def get_module(self) -> str:
        return 'internal'


class HealthCheckRequest(InternalRequest):
    def __init__(self):
        super().__init__()

    def get_request_type(self):
        return "HealthCheckRequest"


class ConnectResetRequest(InternalRequest):
    serverIp: Optional[str]
    serverPort: Optional[str]

    def get_request_type(self) -> str:
        return CONNECTION_RESET_REQUEST_TYPE


class ClientDetectionRequest(InternalRequest):
    def get_request_type(self) -> str:
        return CLIENT_DETECTION_REQUEST_TYPE


class ServerCheckRequest(InternalRequest):

    def get_request_type(self):
        return "ServerCheckRequest"


class ConnectionSetupRequest(InternalRequest):
    clientVersion: Optional[str] = ''
    tenant: Optional[str] = ''
    labels: dict = {}

    def __init__(self, client_version: str, tenant: str, labels: dict):
        super().__init__()
        self.clientVersion = client_version
        self.tenant = tenant
        self.labels = labels

    def get_request_type(self):
        return "ConnectionSetupRequest"
