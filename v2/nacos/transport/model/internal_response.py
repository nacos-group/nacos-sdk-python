from typing import Optional

from v2.nacos.transport.model.rpc_response import Response


class NotifySubscriberResponse(Response):
    def get_response_type(self) -> str:
        return "NotifySubscriberResponse"


class ConnectResetResponse(Response):
    def get_response_type(self) -> str:
        return "ConnectResetResponse"


class ClientDetectionResponse(Response):

    def get_response_type(self) -> str:
        return "ClientDetectionResponse"

class SetupAckResponse(Response):
    def get_response_type(self) -> str:
        return "SetupAckResponse"


class ServerCheckResponse(Response):
    connectionId: Optional[str] = ''
    supportAbilityNegotiation : bool = False

    def get_response_type(self) -> str:
        return "ServerCheckResponse"

    def set_connection_id(self, connection_id: str) -> None:
        self.connectionId = connection_id

    def get_connection_id(self) -> str:
        return self.connectionId


class HealthCheckResponse(Response):
    def get_response_type(self):
        return "HealthCheckResponse"


class ErrorResponse(Response):
    def get_response_type(self):
        return "ErrorResponse"
