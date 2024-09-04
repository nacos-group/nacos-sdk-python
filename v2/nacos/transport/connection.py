from abc import ABC, abstractmethod

from v2.nacos.transport.model.rpc_request import Request
from v2.nacos.transport.model.rpc_response import Response
from v2.nacos.transport.model.server_info import ServerInfo


class IConnection(ABC):
    @abstractmethod
    def request(self, request: Request, timeout_mills: int) -> Response:
        pass

    @abstractmethod
    def close(self):
        pass


class Connection(IConnection, ABC):
    def __init__(self, connection_id, server_info: ServerInfo):
        self.connection_id = connection_id
        self.abandon = False
        self.server_info = server_info

    def get_connection_id(self) -> str:
        return self.connection_id

    def get_server_info(self) -> ServerInfo:
        return self.server_info

    def set_abandon(self, flag: bool):
        self.abandon = flag

    def is_abandon(self):
        return self.abandon
