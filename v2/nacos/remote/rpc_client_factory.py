import logging
from typing import Dict

from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.remote.grpc.grpc_client import GrpcClient
from v2.nacos.remote.rpc_client import RpcClient
from v2.nacos.remote.utils import ConnectionType


class RpcClientFactory:
    def __init__(self, logger):
        self.logger = logger
        self.__CLIENT_MAP = {}

    def get_all_client_entries(self) -> Dict[str, RpcClient]:
        return self.__CLIENT_MAP

    def destroy_client(self, client_name: str):
        if client_name not in self.__CLIENT_MAP.keys():
            raise NacosException("rpc client name error.")
        else:
            rpc_client = self.__CLIENT_MAP[client_name]
            rpc_client.shutdown()

    def get_client(self, client_name: str) -> RpcClient:
        return self.__CLIENT_MAP[client_name]

    def create_client(self, client_name: str, connection_type: str, labels: Dict[str, str]) -> RpcClient:
        client = None
        if client_name not in self.__CLIENT_MAP.keys():
            self.logger.info("[RpcClientFactory]Create a new rpc client of " + str(client_name))
            if connection_type == ConnectionType.GRPC:
                client = GrpcClient(self.logger)
            if not client:
                raise NacosException("Unsupported connection type: " + str(connection_type))
            client.set_labels(labels)
        return client
