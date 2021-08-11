from typing import Dict


class RequestMeta:
    def __init__(self):
        self.__connection_id = ""
        self.__client_ip = ""
        self.__client_version = ""
        self.__labels = {}

    def get_client_version(self) -> str:
        return self.__client_version

    def set_client_version(self, client_version: str) -> None:
        self.__client_version = client_version

    def get_labels(self) -> Dict[str, str]:
        return self.__labels

    def set_labels(self, labels: Dict[str, str]) -> None:
        self.__labels = labels

    def get_connection_id(self) -> str:
        return self.__connection_id

    def set_connection_id(self, connection_id: str) -> None:
        self.__connection_id = connection_id

    def get_client_ip(self) -> str:
        return self.__client_ip

    def set_client_ip(self, client_ip: str) -> None:
        self.__client_ip = client_ip

    def __str__(self):
        return "RequestMeta{connectionId='" + self.__connection_id + "', clientIp='" + self.__client_ip +\
               "', clientVersion='" + "', labels=" + str(self.__labels) + "}"
