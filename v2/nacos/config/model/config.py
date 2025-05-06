import asyncio
from typing import Optional, Callable, List

from pydantic import BaseModel

from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.config.filter.config_filter import ConfigFilterChainManager
from v2.nacos.config.model.config_param import ConfigParam, UsageType


class ConfigItem(BaseModel):
    id: str = ''
    dataId: str = ''
    group: str = ''
    content: str = ''
    md5: Optional[str] = ''
    tenant: str = ''
    appname: str = ''


class ConfigPage(BaseModel):
    totalCount: int = 0
    pageNumber: int = 0
    pagesAvailable: int = 0
    pageItems: List[ConfigItem] = []


class ConfigListenContext(BaseModel):
    group: str = ''
    md5: str = ''
    dataId: str = ''
    tenant: str = ''


class ConfigContext(BaseModel):
    group: str = ''
    dataId: str = ''
    tenant: str = ''


class SubscribeCacheData:
    def __init__(self, data_id: str, group: str, tenant: str, content: str, md5: str,
                 encrypted_data_key: str,
                 chain_manager: ConfigFilterChainManager, content_type: str = '',
                 is_sync_with_server: bool = False):
        self.data_id = data_id
        self.group = group
        self.tenant = tenant
        self.content = content
        self.content_type = content_type
        self.md5 = md5
        self.cache_data_listeners: List[CacheDataListenerWrap] = []
        self.encrypted_data_key = encrypted_data_key
        self.task_id = 0
        self.config_chain_manager = chain_manager
        self.is_sync_with_server = is_sync_with_server
        self.lock = asyncio.Lock()

    async def add_listener(self, listener: Optional[Callable]):
        if listener is None:
            raise NacosException(INVALID_PARAM, "cache data listener is None")
        async with self.lock:
            if any(CacheDataListenerWrap(listener, self.md5) == existing_listener for existing_listener in
                   self.cache_data_listeners):
                return

            self.cache_data_listeners.append(CacheDataListenerWrap(listener, self.md5))

    async def remove_listener(self, listener: Optional[Callable]):
        if listener is None:
            return
        async with self.lock:
            self.cache_data_listeners = [existing_listener for existing_listener in self.cache_data_listeners
                                         if existing_listener.listener != listener]

    async def execute_listener(self):
        async with self.lock:
            for listener_wrap in self.cache_data_listeners:
                if listener_wrap.last_md5 != self.md5:
                    listener_wrap.last_md5 = self.md5
                    param = ConfigParam(data_id=self.data_id,
                                        group=self.group,
                                        content=self.content,
                                        encrypted_data_key=self.encrypted_data_key,
                                        usage_type=UsageType.response_type.value
                                        )
                    self.config_chain_manager.do_filters(param)
                    decrypted_content = param.content
                    await listener_wrap.listener(self.tenant, self.group, self.data_id, decrypted_content)


class CacheDataListenerWrap:
    def __init__(self, listener: Callable, last_md5):
        self.listener = listener
        self.last_md5 = last_md5

    def __eq__(self, other):
        if not isinstance(other, CacheDataListenerWrap):
            return False
        return self.listener == other.listener and self.last_md5 == other.last_md5

    def __hash__(self):
        return hash((self.listener, self.last_md5))
