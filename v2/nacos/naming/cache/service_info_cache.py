import json
import logging
import os
import threading
from datetime import datetime

from v2.nacos.common.constants import Constants
from v2.nacos.common import disk_cache

from v2.nacos.common.client_config import ClientConfig
from v2.nacos.naming.model.service import Service
from v2.nacos.naming.model.service_info import ServiceInfo
from v2.nacos.naming.util.naming_client_util import get_service_cache_key, get_group_name


class ServiceInfoCache:
    def __init__(self, client_config: ClientConfig):
        self.logger = logging.getLogger(Constants.NAMING_MODULE)
        self.cache_dir = os.path.join(client_config.cache_dir, Constants.NAMING_MODULE, client_config.namespace_id)
        self.service_info_map = {}
        self.update_time_map = {}
        self.lock = threading.Lock()

        if not client_config.not_load_cache_at_start:
            self.load_cache_from_disk()

    def load_cache_from_disk(self):
        service_map = disk_cache.read_services_from_file(self.cache_dir)
        if service_map is None or len(service_map) == 0:
            self.logger.info("[load_cache_from_disk] no cache file found, skip loading cache from disk.")
            return

        with self.lock:
            for service_name, service_info in service_map.items():
                self.service_info_map[service_name] = service_info
            self.logger.info("[load_cache_from_disk] loaded {%s} entries cache from disk.", len(service_map))

    def process_service_json(self, data):
        service = json.loads(data)
        self.process_service(service)

    def process_service(self, service: ServiceInfo):
        if service is None:
            return

        if not self.update_cache_when_empty:
            if 'Hosts' not in service or not service['Hosts']:
                # 如果服务实例列表是空的且update_cache_when_empty为假，则跳过更新缓存
                self.logger.warning(
                    f"instance list is empty, skipping update as update_cache_when_empty is set to False. service name: {service['Name']}")
                return

        # 构建cache key，你需要根据其实现自己的获取键的方法
        cache_key = self.get_service_cache_key(service)

        with self.lock:
            old_domain = self.service_info_map.get(cache_key, None)
            if old_domain is not None and old_domain['LastRefTime'] >= service['LastRefTime']:
                self.logger.warning(
                    f"out of date data received, old-t: {old_domain['LastRefTime']}, new-t: {service['LastRefTime']}")
                return

            # 更新时间和服务信息
            self.update_time_map[cache_key] = int(datetime.now().timestamp() * 1000)
            self.service_info_map[cache_key] = service

            if not old_domain or self.check_instance_changed(old_domain, service):
                self.logger.info(f"service key: {cache_key} was updated to: {json.dumps(service)}")
                # 在这里你需要实现将服务信息写到磁盘的功能

                # 触发订阅更新，这里你需要实现订阅逻辑
                # self.sub_callback.service_changed(cache_key, service)

    def get_service_cache_key(self, service):
        # 生成服务的缓存键
        return f"{service['Name']}@{service['Clusters']}"

    def get_service_info(self, service_name, group_name, clusters) -> ServiceInfo:
        cache_key = get_service_cache_key(get_group_name(service_name, group_name), clusters)
        service, ok = self.service_info_map.get(cache_key)
        if ok:
            return service, ok
        else:
            return {}, ok

    def check_instance_changed(self, old_domain, service):
        if old_domain is None:
            return True
        old_service = old_domain
        return self.is_service_instance_changed(old_service, service)

    def is_service_instance_changed(self, old_service: ServiceInfo, new_service: ServiceInfo):
        old_hosts_len = len(old_service['Hosts'])
        new_hosts_len = len(new_service['Hosts'])
        if old_hosts_len != new_hosts_len:
            return True

        old_ref_time = old_service['LastRefTime']
        new_ref_time = new_service['LastRefTime']
        if old_ref_time > new_ref_time:
            self.logger.warning(f"out of date data received, old-t: {old_ref_time}, new-t: {new_ref_time}")
            return False

        # 排序实例列表并比较，函数需要你实现
        old_instance = sorted(old_service['Hosts'])
        new_instance = sorted(new_service['Hosts'])
        return old_instance != new_instance
