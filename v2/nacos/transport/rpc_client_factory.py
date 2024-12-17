import asyncio
from typing import Dict

from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.nacos_exception import NacosException, CLIENT_INVALID_PARAM
from v2.nacos.transport.grpc_client import GrpcClient
from v2.nacos.transport.nacos_server_connector import NacosServerConnector
from v2.nacos.transport.rpc_client import RpcClient, ConnectionType


class RpcClientFactory:

    def __init__(self, logger):
        self.client_map = {}
        self.logger = logger
        self.lock = asyncio.Lock()

    def get_all_client_entries(self) -> Dict[str, RpcClient]:
        return self.client_map

    def get_client(self, client_name: str) -> RpcClient:
        return self.client_map[client_name]

    async def create_client(self, client_name: str, connection_type: ConnectionType, labels: Dict[str, str],
                            client_config: ClientConfig, nacos_server: NacosServerConnector) -> RpcClient:
        async with self.lock:
            client = None
            if client_name not in self.client_map.keys():
                self.logger.info("create new rpc client: " + client_name)
                if connection_type == ConnectionType.GRPC:
                    client = GrpcClient(self.logger, client_name, client_config, nacos_server)

                if not client:
                    raise NacosException(CLIENT_INVALID_PARAM, "unsupported connection type: " + str(connection_type))
                client.put_all_labels(labels)
                self.client_map[client_name] = client
                return client
            return self.client_map[client_name]

    async def shutdown_all_clients(self):
        for client in self.client_map.values():
            await client.shutdown()
