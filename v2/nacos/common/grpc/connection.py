from abc import ABC, abstractmethod
from grpc import Channel
from .remote.rpc_request import IRequest
from .remote.rpc_response import IResponse

class RpcClient:
    pass

class ServerInfo:
    pass

class IConnection(ABC):
    @abstractmethod
    def request(self, request: IRequest, timeout_mills: int, client: RpcClient) -> IResponse:
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def get_connection_id(self) -> str:
        pass

    @abstractmethod
    def get_server_info(self) -> ServerInfo:
        pass

    @abstractmethod
    def set_abandon(self, flag: bool):
        pass

    @abstractmethod
    def get_abandon(self) -> bool:
        pass


class Connection(IConnection):
    def __init__(self, conn: Channel, connection_id: str, server_info: ServerInfo):
        self._conn = conn  # This should be an actual gRPC connection object 
        self._connection_id = connection_id
        self._abandon = False
        self._server_info = server_info

    def request(self, request: IRequest, timeout_mills: int, client: RpcClient) -> IResponse:
        # Implement the request logic here
        pass #考虑去掉这个无用的定义

    def close(self):
        if self._conn:
            self._conn.close()  # Actual gRPC connection close logic

    def get_connection_id(self) -> str:
        return self._connection_id

    def get_server_info(self) -> ServerInfo:
        return self._server_info

    def set_abandon(self, flag: bool):
        self._abandon = flag

    def get_abandon(self) -> bool:
        return self._abandon