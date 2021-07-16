from abc import ABCMeta, abstractmethod
from v2.nacos.remote.irequester import Requester


class Connection(metaclass=ABCMeta, Requester):
    def __init__(self, server_info=None):
        self.__connection_id = ""
        self.__abandon = False
        self.__server_info = server_info # ServerInfo()

    def get_connection_id(self):
        return self.__connection_id

    def set_connection_id(self, connection_id):
        self.__connection_id = connection_id

    def is_abandon(self):
        return self.__abandon

    def set_abandon(self, abandon):
        self.__abandon = abandon
