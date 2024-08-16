from abc import ABC, abstractmethod
from v2.nacos.common.model.request import IRequest
from v2.nacos.common.model.response import IResponse
from v2.nacos.transport.rpc_client import RpcClient

class IConnection(ABC):
    @abstractmethod
    def request(self, request: IRequest, timeout_mills: int, client: RpcClient) -> IResponse:
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def get_connection_id(self):
        pass

    @abstractmethod
    def get_server_info(self):
        pass

    @abstractmethod
    def set_abandon(self, flag: bool):
        pass

    @abstractmethod
    def get_abandon(self):
        pass


class Connection(IConnection):
    def __init__(self, conn, connection_id, server_info, abandon):
        self._conn = conn  
        self._connection_id = connection_id
        self._abandon = abandon
        self._server_info = server_info

    def request(self, request, timeout_mills, client):
        pass 

    def close(self):
        if self._conn:
            self._conn.close()  

    def get_connection_id(self) -> str:
        return self._connection_id

    def get_server_info(self):
        return self._server_info

    def set_abandon(self, flag: bool):
        self._abandon = flag

    def get_abandon(self):
        return self._abandon