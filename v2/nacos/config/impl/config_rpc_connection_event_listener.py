import queue

from v2.nacos.remote.iconnection_event_listener import ConnectionEventListener
from v2.nacos.remote.rpc_client import RpcClient


class ConfigRpcConnectionEventListener(ConnectionEventListener):
    def __init__(self, logger, rpc_client_inner: RpcClient, cache_map: dict, notify_listen_config):
        self.logger = logger
        self.rpc_client = rpc_client_inner
        self.cache_map = cache_map
        self.notify_listen_config = notify_listen_config

    def on_connected(self) -> None:
        self.logger.info("[%s] Connected, notify listen context..." % self.rpc_client.get_name())
        self.notify_listen_config()

    def on_disconnect(self) -> None:
        if "taskId" in self.rpc_client.get_labels().keys():
            task_id = self.rpc_client.get_labels()["taskId"]
            self.logger.info("[%s] Disconnected, clear listen context..." % self.rpc_client.get_name())
            for cache_data in self.cache_map.values():
                if cache_data.task_id == int(task_id):
                    cache_data.set_sync_with_server(False)
                    continue
                else:
                    cache_data.set_sync_with_server(False)
