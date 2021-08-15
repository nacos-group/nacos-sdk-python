import urllib.parse

from v2.nacos.common.constants import Constants
from v2.nacos.common.utils import get_current_time_millis
from v2.nacos.exception.nacos_exception import NacosException


class ServiceInfo:
    EMPTY = ""
    ALL_IPS = "000--00-ALL_IPS--00--000"
    SPLITER = "@@"
    DEFAULT_CHARSET = "UTF-8"

    def __init__(self, key=None):
        self.name = ""
        self.group_name = ""
        self.clusters = ""
        self.cache_millis = 1000
        self.hosts = []
        self.last_ref_time = 0
        self.checksum = ""
        self.all_ips = False
        self.reach_protection_threshold = False
        self.json_from_server = ServiceInfo.EMPTY

        if key:
            max_index = 2
            cluster_index = 2
            service_name_index = 1
            group_index = 0
            keys = key.split(Constants.SERVICE_INFO_SPLITER)
            if len(keys) >= max_index + 1:
                self.group_name = keys[group_index]
                self.name = keys[service_name_index]
                self.clusters = keys[cluster_index]
            elif len(keys) == max_index:
                self.group_name = keys[group_index]
                self.name = keys[service_name_index]
            else:
                raise NacosException("Can't parse out 'group_name', but it must not None!")

    def ip_count(self):
        return self.hosts.count()

    def expired(self):
        return get_current_time_millis() - self.last_ref_time > self.cache_millis

    def set_hosts(self, hosts):
        self.hosts = hosts

    def add_host(self, host):
        self.hosts.append(host)

    def add_all_hosts(self, hosts):
        self.hosts.extend(hosts)

    def get_hosts(self):
        return self.hosts

    def is_valid(self):
        return self.hosts != []

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_group_name(self):
        return self.group_name

    def set_group_name(self, group_name):
        self.group_name = group_name

    def get_last_ref_time(self):
        return self.last_ref_time

    def set_last_ref_time(self, last_ref_time):
        self.last_ref_time = last_ref_time

    def get_clusters(self):
        return self.clusters

    def set_clusters(self, clusters):
        self.clusters = clusters

    def get_cache_millis(self):
        return self.cache_millis

    def set_cache_millis(self, cache_millis):
        self.cache_millis = cache_millis

    def get_json_from_server(self) -> str:
        return self.json_from_server

    def set_json_from_server(self, json_from_server) -> None:
        self.json_from_server = json_from_server

    def validate(self):
        if self.all_ips:
            return True

        if not self.hosts:
            return False

        valid_hosts = []
        for host in self.hosts:
            if not host.is_healthy():
                continue

            for i in range(host.get_weight()):
                valid_hosts.append(i)

        return valid_hosts.count() > 0

    @staticmethod
    def get_key(name=None, clusters=None):
        if clusters and len(clusters.strip()) > 0:
            return name + Constants.SERVICE_INFO_SPLITER + clusters
        return name

    def get_key_encoded(self):
        service_name = self.get_grouped_service_name().encode(ServiceInfo.DEFAULT_CHARSET)
        service_name = urllib.parse.quote(service_name)
        return self.get_key(service_name, self.clusters)

    def get_grouped_service_name(self):
        service_name = self.name
        if self.group_name and Constants.SERVICE_INFO_SPLITER not in service_name:
            service_name = self.group_name + Constants.SERVICE_INFO_SPLITER + service_name
        return service_name
