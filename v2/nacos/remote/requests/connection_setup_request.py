from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type
from v2.nacos.ability import client_abilities


class ConnectionSetupRequest(request.Request):
    def __init__(self):
        super().__init__()
        self.__client_version = ""
        self.__client_abilities = None
        self.__abilities = client_abilities.ClientAbilities()
        self.__tenant = ""
        self.__labels = {}

        self.__MODULE = "internal"

    def get_client_version(self):
        return self.__client_version

    def set_client_version(self, client_version):
        self.__client_version = client_version

    def get_labels(self):
        return self.__labels

    def set_labels(self, labels):
        self.__labels = labels

    def get_tenant(self):
        return self.__tenant

    def set_tenant(self, tenant):
        self.__tenant = tenant

    def get_abilities(self):
        return self.__abilities

    def set_abilities(self, abilities):
        self.__abilities = abilities

    def get_module(self):
        return self.__MODULE

    def get_remote_type(self):
        return remote_request_type["ConnectionSetup"]