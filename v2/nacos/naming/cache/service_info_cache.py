import json
import logging
import os
import threading

from v2.nacos.naming.cache import disk_cache

from v2.nacos.config.client_config import ClientConfig


class ServiceInfoCache:
    JM_SNAPSHOT_PATH_PROPERTY = "JM.SNAPSHOT.PATH"

    FILE_PATH_NACOS = "nacos"

    FILE_PATH_NAMING = "naming"

    USER_HOME_PROPERTY = "user.home"

    def __init__(self, client_config: ClientConfig):
        self.logger = logging.getLogger(__name__)
        self.cache_dir = os.path.join(client_config.cache_dir, "naming", client_config.namespace_id)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.logger.info(f"naming cache dir: {self.cache_dir}.")

        self.__init_cache_dir(namespace, properties)
        self.lock = threading.RLock()

        if not client_config.not_load_cache_at_start:
            self.load_cache_from_disk()
        else:
            self.service_info_map = {}

    def load_cache_from_disk(self):
        temp_service_info_map = disk_cache.read_services_from_file(self.cache_dir)
        with self.lock:
            self.service_info_map = temp_service_info_map

    def __init_cache_dir(self, namespace, properties):
        jm_snapshot_path = os.environ.get(ServiceInfoCache.JM_SNAPSHOT_PATH_PROPERTY)
        naming_cache_registry_dir = ""

        if PropertyKeyConstants.NAMING_CACHE_REGISTRY_DIR in properties:
            naming_cache_registry_dir = os.path.join(properties[PropertyKeyConstants.NAMING_CACHE_REGISTRY_DIR])

        if jm_snapshot_path.strip():
            self.cache_dir = os.path.join(jm_snapshot_path,
                                          ServiceInfoHolder.FILE_PATH_NACOS + naming_cache_registry_dir,
                                          ServiceInfoHolder.FILE_PATH_NAMING,
                                          namespace)
        else:
            self.cache_dir = os.path.join(os.environ.get(ServiceInfoHolder.USER_HOME_PROPERTY),
                                          ServiceInfoHolder.FILE_PATH_NACOS + naming_cache_registry_dir,
                                          ServiceInfoHolder.FILE_PATH_NAMING,
                                          namespace)

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
