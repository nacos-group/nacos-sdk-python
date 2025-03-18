import asyncio
import os
from typing import Dict

from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.nacos_exception import NacosException, CLIENT_INVALID_PARAM, INVALID_PARAM
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

                self.logger.info(f"init app conn labels from client config,{client_config.app_conn_labels}")
                app_conn_labels_env = get_app_labels_from_env()
                self.logger.info(f"init app conn labels from env,{app_conn_labels_env}")
                app_conn_labels = merge_app_labels(client_config.app_conn_labels, app_conn_labels_env)
                self.logger.info("final app conn labels: " + str(app_conn_labels))
                app_conn_labels = add_prefix_for_each_key(app_conn_labels, "app_")
                if len(app_conn_labels) > 0:
                    client.put_all_labels(app_conn_labels)

                client.put_all_labels(labels)
                self.client_map[client_name] = client
                return client
            return self.client_map[client_name]

    async def shutdown_all_clients(self):
        for client in self.client_map.values():
            await client.shutdown()


def get_app_labels_from_env() -> dict:
    config_map = {}
    # nacos_config_gray_label
    gray_label = os.getenv("nacos_config_gray_label")
    if gray_label:
        config_map["nacos_config_gray_label"] = gray_label

    # nacos_app_conn_labels
    conn_labels = os.getenv("nacos_app_conn_labels")
    if conn_labels:
        labels_map = parse_labels(conn_labels)
        config_map.update(labels_map)

    return config_map


def parse_labels(raw_labels: str) -> dict:
    if not raw_labels.strip():
        return {}

    result_map = {}
    labels = raw_labels.split(",")
    for label in labels:
        if label.strip():
            kv = label.split("=")
            if len(kv) == 2:
                key = kv[0].strip()
                value = kv[1].strip()
                result_map[key] = value
            else:
                raise NacosException(INVALID_PARAM, f"unknown label format: {label}")
    return result_map


def merge_app_labels(app_labels_appointed: dict, app_labels_env: dict) -> dict:
    preferred = os.getenv("nacos_app_conn_labels_preferred", "").lower()
    prefer_first = preferred != "env"
    return merge_maps(app_labels_appointed, app_labels_env, prefer_first)


def merge_maps(map1: dict, map2: dict, prefer_first: bool) -> dict:
    result = {}  # Start with map1
    if map1:
        result.update(map1)

    for k, v in map2.items():
        if not (prefer_first and k in result):
            result[k] = v

    return result


def add_prefix_for_each_key(m: dict, prefix: str) -> dict:
    if not m:
        return m

    new_map = {}
    for k, v in m.items():
        if k.strip():
            new_key = prefix + k
            new_map[new_key] = v
    return new_map
