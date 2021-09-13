import json
import logging
import os

from v2.nacos.common.lifecycle.closeable import Closeable
from v2.nacos.naming.backups.failover_reactor import FailoverReactor
from v2.nacos.naming.cache.disk_cache import DiskCache
from v2.nacos.naming.dtos.service_info import ServiceInfo
from v2.nacos.naming.utils.naming_utils import NamingUtils
from v2.nacos.property_key_constants import PropertyKeyConstants


class ServiceInfoHolder(Closeable):
    JM_SNAPSHOT_PATH_PROPERTY = "JM.SNAPSHOT.PATH"

    FILE_PATH_NACOS = "nacos"

    FILE_PATH_NAMING = "naming"

    USER_HOME_PROPERTY = "user.home"

    def __init__(self, logger, namespace, properties):
        self.logger = logger

        self.__init_cache_dir(namespace, properties)
        if self.__is_load_cache_at_start(properties):
            self.service_info_map = DiskCache.read(self.cache_dir)
        else:
            self.service_info_map = {}

        self.failover_reactor = FailoverReactor(self, self.cache_dir)
        self.push_empty_protection = self.__is_push_empty_protect(properties)

    def __init_cache_dir(self, namespace, properties):
        # jm_snapshot_path = os.environ.get(ServiceInfoHolder.JM_SNAPSHOT_PATH_PROPERTY)
        # naming_cache_registry_dir = ""
        #
        # if PropertyKeyConstants.NAMING_CACHE_REGISTRY_DIR in properties:
        #     naming_cache_registry_dir = os.path.join(properties[PropertyKeyConstants.NAMING_CACHE_REGISTRY_DIR])
        #
        # if jm_snapshot_path and jm_snapshot_path.strip():
        #     self.cache_dir = os.path.join(jm_snapshot_path,
        #                                   ServiceInfoHolder.FILE_PATH_NACOS + naming_cache_registry_dir,
        #                                   ServiceInfoHolder.FILE_PATH_NAMING,
        #                                   namespace)
        # else:
        #     self.cache_dir = os.path.join(os.environ.get(ServiceInfoHolder.USER_HOME_PROPERTY),
        #                                   ServiceInfoHolder.FILE_PATH_NACOS + naming_cache_registry_dir,
        #                                   ServiceInfoHolder.FILE_PATH_NAMING,
        #                                   namespace)

        # todo
        self.cache_dir = "/Users/cangxiamy/nacos/data"

    @staticmethod
    def __is_load_cache_at_start(properties):
        load_cache_at_start = False
        if PropertyKeyConstants.NAMING_LOAD_CACHE_AT_START in properties.keys():
            load_cache_at_start = properties[PropertyKeyConstants.NAMING_LOAD_CACHE_AT_START]
        return load_cache_at_start

    @staticmethod
    def __is_push_empty_protect(properties):
        push_empty_protection = False
        if properties and PropertyKeyConstants.NAMING_PUSH_EMPTY_PROTECTION in properties.keys():
            push_empty_protection = properties[PropertyKeyConstants.NAMING_PUSH_EMPTY_PROTECTION]

        return push_empty_protection

    def get_service_info_map(self) -> dict:
        return self.service_info_map

    def get_service_info(self, service_name, group_name, clusters):
        self.logger.debug("Failover-mode: " + self.failover_reactor.is_failover_switch())
        grouped_service_name = NamingUtils.get_grouped_name(service_name, group_name)
        key = ServiceInfo.get_key(grouped_service_name, clusters)
        if self.failover_reactor.is_failover_switch():
            return self.failover_reactor.get_service(key)
        return self.service_info_map[key]

    def process_service_info(self, service_info: ServiceInfo) -> ServiceInfo:
        service_key = service_info.get_key()
        if not service_key:
            return

        old_service = self.service_info_map[service_key]
        if self.__is_empty_or_error_push(service_info):
            return old_service

        self.service_info_map[service_key] = service_info
        changed = self.__is_changed_service_info(old_service, service_info)
        if not service_info.get_json_from_server().strip():
            service_info.set_json_from_server(json.dumps(service_info))
        if changed:
            self.logger.info("Current ips:(" + service_info.ip_count() + ") service: " + service_info.get_key() + \
                             " -> " + json.dumps(service_info.get_hosts()))
            # todo notifier
            DiskCache.write(service_info, self.cache_dir)

        return service_info

    def __is_empty_or_error_push(self, service_info: ServiceInfo) -> bool:
        return service_info.get_hosts() == [] or (self.push_empty_protection and not service_info.validate())

    def __is_changed_service_info(self, old_service: ServiceInfo, new_service: ServiceInfo) -> bool:
        if not old_service:
            self.logger.info("init new ips(" + new_service.ip_count() + ") service: " + new_service.get_key() + \
                             " -> " + json.dumps(new_service.get_hosts()))
            return True

        if old_service.get_last_ref_time() > new_service.get_last_ref_time():
            self.logger.info("out of date received, old-t" + old_service.get_last_ref_time() + \
                             ", new-t: " + new_service.get_last_ref_time())

        changed = False
        old_host_map = {}
        for host in old_service.get_hosts():
            old_host_map[host.to_inet_adder()] = host

        new_host_map = {}
        for host in new_service.get_hosts():
            new_host_map[host.to_inet_adder()] = host

        mod_host = []
        new_host = []
        rmv_host = []

        for key, value in new_host_map.items():
            if key in old_host_map.keys() and str(value) != str(old_host_map[key]):
                mod_host.append(value)
                continue

            if key not in old_host_map.keys():
                new_host.append(value)

        for key, value in old_host_map.items():
            if key in new_host_map.keys():
                continue
            else:
                rmv_host.append(value)

        if len(new_host) > 0:
            changed = True
            self.logger.info("new ips(" + str(len(new_host)) + ") service: " + new_service.get_key() + " -> " + \
                             json.dumps(new_host))

        if len(rmv_host) > 0:
            changed = True
            self.logger.info("new ips(" + str(len(rmv_host)) + ") service: " + new_service.get_key() + " -> " + \
                             json.dumps(rmv_host))

        if len(mod_host) > 0:
            changed = True
            self.logger.info("new ips(" + str(len(mod_host)) + ") service: " + new_service.get_key() + " -> " + \
                             json.dumps(mod_host))

        return changed

    def shutdown(self) -> None:
        self.logger.info("%s do shutdown begin", self.__class__.__name__)
        self.failover_reactor.shutdown()
        self.logger.info("%s do shutdown stop", self.__class__.__name__)
