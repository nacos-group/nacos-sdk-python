import asyncio
from typing import Dict, List, Callable

from v2.nacos.naming.cache.subscribe_callback_wrapper import \
    SubscribeCallbackFuncWrapper
from v2.nacos.naming.model.service import Service
from v2.nacos.naming.util.naming_client_util import get_service_cache_key


class SubscribeManager:
    def __init__(self):
        self.callback_func_wrapper_map: Dict[str, List[SubscribeCallbackFuncWrapper]] = {}
        self.mux = asyncio.Lock()

    async def is_subscribed(self, service_name: str, clusters: str) -> bool:
        key = get_service_cache_key(service_name, clusters)
        return key in self.callback_func_wrapper_map

    async def add_callback_func(self, service_name: str, clusters: str, callback_func_wrapper: SubscribeCallbackFuncWrapper):
        key = get_service_cache_key(service_name, clusters)
        async with self.mux:
            if key not in self.callback_func_wrapper_map:
                self.callback_func_wrapper_map[key] = []
            self.callback_func_wrapper_map[key].append(callback_func_wrapper)

    async def remove_callback_func(self, service_name: str, clusters: str, callback_func_wrapper: SubscribeCallbackFuncWrapper):
        key = get_service_cache_key(service_name, clusters)
        async with self.mux:
            if key in self.callback_func_wrapper_map:
                self.callback_func_wrapper_map[key] = [func for func in self.callback_func_wrapper_map[key]
                                                       if func.callback_func != callback_func_wrapper.callback_func
                                                       or func.selector != callback_func_wrapper.selector]
                if not self.callback_func_wrapper_map[key]:
                    del self.callback_func_wrapper_map[key]

    async def service_changed(self, cache_key: str, service: Service):
        if cache_key in self.callback_func_wrapper_map:
            for callback_func in self.callback_func_wrapper_map[cache_key]:
                await callback_func.notify_listener(service)
