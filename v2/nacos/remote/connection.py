from abc import ABCMeta, abstractmethod
from v2.nacos.remote.irequester import Requester
from v2.nacos.remote.rpc_client import ServerInfo


class Connection(Requester, metaclass=ABCMeta):
    def __init__(self, server_info: ServerInfo):
        self.__connection_id = ""
        self.__abandon = False
        self.__server_info = server_info

    def get_connection_id(self) -> str:
        return self.__connection_id

    def set_connection_id(self, connection_id: str) -> None:
        self.__connection_id = connection_id

    def is_abandon(self) -> bool:
        return self.__abandon

    def set_abandon(self, abandon: bool) -> None:
        self.__abandon = abandon

    def get_server_info(self) -> ServerInfo:
        return self.__server_info
