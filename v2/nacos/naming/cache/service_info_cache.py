import asyncio
import json
import logging
import os
from typing import Callable, Optional, List, Dict

from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.constants import Constants
from v2.nacos.naming.cache.subscribe_callback_wrapper import \
    SubscribeCallbackFuncWrapper
from v2.nacos.naming.cache.subscribe_manager import SubscribeManager
from v2.nacos.naming.model.instance import Instance
from v2.nacos.naming.model.service import Service
from v2.nacos.naming.util.naming_client_util import get_service_cache_key, get_group_name
from v2.nacos.utils.common_util import get_current_time_millis, to_json_string
from v2.nacos.utils.file_util import read_all_files_in_dir, write_to_file


class ServiceInfoCache:
    def __init__(self, client_config: ClientConfig):
        self.logger = logging.getLogger(Constants.NAMING_MODULE)
        self.cache_dir = os.path.join(client_config.cache_dir, Constants.NAMING_MODULE, client_config.namespace_id)
        self.service_info_map: Dict[str, Service] = {}
        self.update_time_map = {}
        self.lock = asyncio.Lock()
        self.sub_callback_manager = SubscribeManager()
        self.update_cache_when_empty = client_config.update_cache_when_empty
        if client_config.load_cache_at_start:
            asyncio.create_task(self.load_cache_from_disk())

    async def load_cache_from_disk(self):
        cache_file_content_dict = await read_all_files_in_dir(self.logger, self.cache_dir)
        if cache_file_content_dict is None:
            return

        service_map = {}
        for file_name, cache_content in cache_file_content_dict.items():
            try:
                service_data = json.loads(cache_content)
                service = Service(**service_data)

                if len(service.hosts) == 0:
                    self.logger.warning(
                        f"instance cache list for service:{service.name} is empty, json string:{cache_content}")

                if service is None:
                    continue
                cache_key = get_service_cache_key(get_group_name(service.name, service.groupName), service.clusters)
                service_map[cache_key] = service
            except json.JSONDecodeError as e:
                self.logger.error(f"failed to parse json:{cache_content}, err:{e}")
                continue
        self.logger.info(f"finish loading name cache, total file size: {len(cache_file_content_dict)}")

        if service_map is None or len(service_map) == 0:
            self.logger.info("[load_cache_from_disk] no cache file found, skip loading cache from disk.")
            return

        self.service_info_map = service_map
        self.logger.info("[load_cache_from_disk] loaded {%s} entries cache from disk.", len(service_map))

    async def process_service_json(self, data: str):
        try:
            service_data = json.loads(data)
            service = Service(**service_data)

            if service is None:
                return
        except json.JSONDecodeError as e:
            self.logger.error(f"failed to parse json:{data}, err:{e}")
            return
        await self.process_service(service)

    async def process_service(self, service: Service):
        if service is None:
            return

        if not self.update_cache_when_empty and len(service.hosts) == 0:
            # 如果服务实例列表是空的且update_cache_when_empty为假，则跳过更新缓存
            self.logger.warning(
                f"instance list is empty, skipping update as update_cache_when_empty is set to False. service name: {service.name}")
            return

        cache_key = get_service_cache_key(get_group_name(service.name, service.groupName), service.clusters)

        async with self.lock:
            old_service = self.service_info_map.get(cache_key, None)
            if old_service is not None and old_service.lastRefTime >= service.lastRefTime:
                self.logger.warning(
                    f"out of date data received, old-t: {old_service.lastRefTime}, new-t: {service.lastRefTime}")
                return

            # 更新时间和服务信息
            self.update_time_map[cache_key] = get_current_time_millis()
            self.service_info_map[cache_key] = service

            if not old_service or self.check_instance_changed(old_service, service):
                self.logger.info(f"service key: {cache_key} was updated to: {str(service)}")
                await write_to_file(self.logger, os.path.join(self.cache_dir, cache_key), to_json_string(service))
                await self.sub_callback_manager.service_changed(cache_key, service)
            self.logger.info(f"current service map size: {len(self.service_info_map)}")

    async def get_service_info(self, service_name, group_name, clusters) -> Service:
        cache_key = get_service_cache_key(get_group_name(service_name, group_name), clusters)
        async with self.lock:
            service = self.service_info_map.get(cache_key)
            self.logger.info(
                f"get service info from cache, key: {cache_key}，instances:{service.hosts if service is not None else 'None'}")
            return service

    def check_instance_changed(self, old_service: Optional[Service], new_service: Service):
        if old_service is None:
            return True
        if len(old_service.hosts) != len(new_service.hosts):
            return True

        old_ref_time = old_service.lastRefTime
        new_ref_time = new_service.lastRefTime
        if old_ref_time > new_ref_time:
            self.logger.warning(f"out of date data received, old-t: {old_ref_time}, new-t: {new_ref_time}")
            return False

        # 排序实例列表并比较，函数需要你实现
        old_instance = self.sort_instances(old_service.hosts)
        new_instance = self.sort_instances(new_service.hosts)
        return old_instance != new_instance

    @staticmethod
    def sort_instances(instances: List[Instance]) -> List[Instance]:
        def instance_key(instance: Instance) -> (int, int):
            ip_num = int(''.join(instance.ip.split('.')))
            return ip_num, instance.port

        return sorted(instances, key=instance_key)

    async def register_callback(self, service_name: str, clusters: str, callback_func_wrapper: SubscribeCallbackFuncWrapper):
        await self.sub_callback_manager.add_callback_func(service_name, clusters, callback_func_wrapper)

    async def deregister_callback(self, service_name: str, clusters: str, callback_func_wrapper: SubscribeCallbackFuncWrapper):
        await self.sub_callback_manager.remove_callback_func(service_name, clusters, callback_func_wrapper)

    async def is_subscribed(self, service_name: str, clusters: str) -> bool:
        return await self.sub_callback_manager.is_subscribed(service_name, clusters)
