import asyncio

from v2.nacos.config.cache.config_subscribe_manager import ConfigSubscribeManager
from v2.nacos.transport.connection_event_listener import ConnectionEventListener
from v2.nacos.transport.rpc_client import RpcClient


class ConfigGrpcConnectionEventListener(ConnectionEventListener):

    def __init__(self, logger, config_subscribe_manager: ConfigSubscribeManager,
                 execute_config_listen_channel: asyncio.Queue, rpc_client: RpcClient):
        self.logger = logger
        self.config_subscribe_manager = config_subscribe_manager
        self.execute_config_listen_channel = execute_config_listen_channel
        self.rpc_client = rpc_client

    async def on_connected(self) -> None:
        self.logger.info(f"{self.rpc_client.name} rpc client connected,notify listen config")
        await self.execute_config_listen_channel.put(None)

    async def on_disconnect(self) -> None:
        task_id = self.rpc_client.labels["taskId"]
        await self.config_subscribe_manager.batch_set_config_changed(int(task_id))
