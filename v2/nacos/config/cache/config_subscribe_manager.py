import asyncio
from logging import Logger
from typing import Optional, Callable, List, Dict

from v2.nacos.common.constants import Constants
from v2.nacos.config.cache.config_info_cache import ConfigInfoCache
from v2.nacos.config.filter.config_filter import ConfigFilterChainManager
from v2.nacos.config.model.config import SubscribeCacheData
from v2.nacos.config.util.config_client_util import get_config_cache_key
from v2.nacos.utils import md5_util
from v2.nacos.utils.md5_util import md5


class ConfigSubscribeManager:
    def __init__(self, logger: Logger, config_info_cache: ConfigInfoCache, namespace_id: str,
                 config_filter_chain_manager: ConfigFilterChainManager,
                 execute_config_listen_channel: asyncio.Queue):
        self.subscribe_cache_map: Dict[str, SubscribeCacheData] = {}
        self.logger = logger
        self.lock = asyncio.Lock()
        self.namespace_id = namespace_id
        self.config_filter_chain_manager = config_filter_chain_manager
        self.config_info_cache = config_info_cache
        self.execute_config_listen_channel = execute_config_listen_channel

    async def add_listener(self, data_id: str, group_name: str, tenant: str,
                           listener: Optional[Callable]):
        cache_key = get_config_cache_key(data_id, group_name, tenant)
        async with self.lock:
            if cache_key in self.subscribe_cache_map:
                subscribe_cache = self.subscribe_cache_map[cache_key]
            else:
                content, encrypted_data_key = await self.config_info_cache.get_config_cache(data_id, group_name)
                md5_str = md5_util.md5(content)
                subscribe_cache = SubscribeCacheData(
                    data_id=data_id,
                    group=group_name,
                    tenant=self.namespace_id,
                    content=content,
                    md5=md5_str,
                    chain_manager=self.config_filter_chain_manager,
                    encrypted_data_key=encrypted_data_key)
                subscribe_cache.task_id = len(self.subscribe_cache_map) // Constants.PER_TASK_CONFIG_SIZE
                self.subscribe_cache_map[cache_key] = subscribe_cache
        await subscribe_cache.add_listener(listener)

    async def remove_listener(self, data_id: str, group_name: str, tenant: str, listener: Optional[Callable]):
        if listener is None:
            return
        cache_key = get_config_cache_key(data_id, group_name, tenant)
        async with self.lock:
            subscribe_cache = self.subscribe_cache_map.get(cache_key)
            if not subscribe_cache:
                return

        await subscribe_cache.remove_listener(listener)

    async def notify_config_changed(self, data_id: str, group_name: str, tenant: str):
        cache_key = get_config_cache_key(data_id, group_name, tenant)
        async with self.lock:
            subscribe_cache = self.subscribe_cache_map.get(cache_key)
            if not subscribe_cache:
                return
        async with subscribe_cache.lock:
            subscribe_cache.is_sync_with_server = False
            self.subscribe_cache_map[cache_key] = subscribe_cache

        await self.execute_config_listen_channel.put(None)

    async def batch_set_config_changed(self, task_id: int):
        for cache_data in self.subscribe_cache_map.values():
            if cache_data.task_id == task_id:
                async with cache_data.lock:
                    cache_data.is_sync_with_server = False

    async def update_subscribe_cache(self, data_id: str, group_name: str, tenant: str, content: str,
                                     encrypted_data_key: str):
        cache_key = get_config_cache_key(data_id, group_name, tenant)
        async with self.lock:
            subscribe_cache = self.subscribe_cache_map.get(cache_key)
            if not subscribe_cache:
                return
            subscribe_cache.content = content
            subscribe_cache.encrypted_data_key = encrypted_data_key
            subscribe_cache.md5 = md5(content)
            subscribe_cache.is_sync_with_server = True

        await subscribe_cache.execute_listener()

    async def execute_listener_and_build_tasks(self, is_sync_all: bool):
        listen_fetch_task_map: Dict[int, List[SubscribeCacheData]] = {}
        for cache_data in self.subscribe_cache_map.values():
            if cache_data.is_sync_with_server:
                await cache_data.execute_listener()
                if not is_sync_all:
                    continue
            if cache_data.task_id not in listen_fetch_task_map:
                listen_fetch_task_map[cache_data.task_id] = []
            listen_fetch_task_map[cache_data.task_id].append(cache_data)
        return listen_fetch_task_map
