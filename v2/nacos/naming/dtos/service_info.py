import urllib.parse
from typing import Optional

from pydantic import BaseModel

from v2.nacos.common.constants import Constants
from v2.nacos.common.utils import get_current_time_millis
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.naming.dtos.instance import Instance


class ServiceInfo(BaseModel):
    name: Optional[str]
    groupName: Optional[str]

    clusters: Optional[str]
    cacheMillis: int = 1000
    hosts: list = []
    lastRefTime: int = 0
    checksum: str = ""
    allIps: bool = False
    reachProtectionThreshold: bool = False
    jsonFromServer: str = ""

    EMPTY = ""

    ALL_IPS = "000--00-ALL_IPS--00--000"

    SPLITER = "@@"

    DEFAULT_CHARSET = "UTF-8"

    def init_from_key(self, key=None):
        if key:
            max_index = 2
            cluster_index = 2
            service_name_index = 1
            group_index = 0
            keys = key.split(Constants.SERVICE_INFO_SPLITER)
            if len(keys) >= max_index + 1:
                self.groupName = keys[group_index]
                self.name = keys[service_name_index]
                self.clusters = keys[cluster_index]
            elif len(keys) == max_index:
                self.groupName = keys[group_index]
                self.name = keys[service_name_index]
            else:
                raise NacosException("Can't parse out 'group_name', but it must not None!")

    def ip_count(self):
        return len(self.hosts)

    def expired(self):
        return get_current_time_millis() - self.lastRefTime > self.cacheMillis

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
        return self.groupName

    def set_group_name(self, group_name):
        self.groupName = group_name

    def get_last_ref_time(self):
        return self.lastRefTime

    def set_last_ref_time(self, last_ref_time):
        self.lastRefTime = last_ref_time

    def get_clusters(self):
        return self.clusters

    def set_clusters(self, clusters):
        self.clusters = clusters

    def get_cache_millis(self):
        return self.cacheMillis

    def set_cache_millis(self, cache_millis):
        self.cacheMillis = cache_millis

    def get_json_from_server(self) -> str:
        return self.jsonFromServer

    def set_json_from_server(self, json_from_server) -> None:
        self.jsonFromServer = json_from_server

    def validate(self):
        if self.allIps:
            return True

        if not self.hosts:
            return False

        valid_hosts = []
        for host in self.hosts:
            if not host.is_healthy():
                continue

            for i in range(host.get_weight()):
                valid_hosts.append(i)

        return len(valid_hosts) > 0

    @staticmethod
    def get_key(name, clusters):
        if clusters and len(clusters.strip()) > 0:
            return name + Constants.SERVICE_INFO_SPLITER + clusters
        return name

    def get_key_default(self):
        service_name = self.get_grouped_service_name()
        return self.get_key(service_name, self.clusters)

    def get_key_encoded(self):
        service_name = self.get_grouped_service_name().encode("utf-8")
        service_name = urllib.parse.quote(service_name)
        return self.get_key(service_name, self.clusters)

    def get_grouped_service_name(self):
        service_name = self.name
        if self.groupName and Constants.SERVICE_INFO_SPLITER not in service_name:
            service_name = self.groupName + Constants.SERVICE_INFO_SPLITER + service_name
        return service_name

    @staticmethod
    def from_key(key: str):
        service_info = ServiceInfo()
        max_seg_count = 3
        segs = key.split(Constants.SERVICE_INFO_SPLITER)
        if len(segs) == max_seg_count - 1:
            service_info.set_group_name(segs[0])
            service_info.set_name(segs[1])
        elif len(segs) == max_seg_count:
            service_info.set_group_name(segs[0])
            service_info.set_name(segs[1])
            service_info.set_clusters(segs[2])
        return service_info

    def __str__(self):
        return self.get_key()

    def get_checksum(self) -> str:
        return self.checksum

    def set_checksum(self, checksum: str) -> None:
        self.checksum = checksum

    def is_reach_protection_threshold(self) -> bool:
        return self.reachProtectionThreshold

    def set_reach_protection_threshold(self, reach_protection_threshold: bool) -> None:
        self.reachProtectionThreshold = reach_protection_threshold

    @staticmethod
    def build(json_dict: dict):
        new_service_info = ServiceInfo(**json_dict)
        hosts_dict_list = new_service_info.get_hosts()
        hosts_instance_list = []
        for host in hosts_dict_list:
            instance = Instance(**host)
            hosts_instance_list.append(instance)
        new_service_info.hosts = hosts_instance_list
        return new_service_info

    def get_hosts_str(self):
        hosts_str = ""
        for host in self.hosts:
            hosts_str += host.json() + ";"
        return hosts_str

    class Config:
        arbitrary_types_allowed = True
