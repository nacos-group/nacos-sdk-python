from typing import List, Dict
import time

class State:
    Running = 0
    Shutdown = 1

class Instance:
    def __init__(self, instance_id: str, ip: str, port: int, weight: float, healthy: bool, enable: bool, ephemeral: bool, cluster_name: str, service_name: str, metadata: Dict[str, str], instance_heart_beat_interval: int, ip_delete_timeout: int, instance_heart_beat_time_out: int):
        self.instance_id = instance_id
        self.ip = ip
        self.port = port
        self.weight = weight
        self.healthy = healthy
        self.enable = enable
        self.ephemeral = ephemeral
        self.cluster_name = cluster_name
        self.service_name = service_name
        self.metadata = metadata
        self.instance_heart_beat_interval = instance_heart_beat_interval
        self.ip_delete_timeout = ip_delete_timeout
        self.instance_heart_beat_time_out = instance_heart_beat_time_out

class Service:
    def __init__(self, cache_millis: int, hosts: List[Instance], checksum: str, last_ref_time: int, clusters: str, name: str, group_name: str, valid: bool, all_ips: bool, reach_protection_threshold: bool):
        self.cache_millis = cache_millis
        self.hosts = hosts
        self.checksum = checksum
        self.last_ref_time = last_ref_time
        self.clusters = clusters
        self.name = name
        self.group_name = group_name
        self.valid = valid
        self.all_ips = all_ips
        self.reach_protection_threshold = reach_protection_threshold

class ServiceDetail:
    def __init__(self, service: 'ServiceInfo', clusters: List['Cluster']):
        self.service = service
        self.clusters = clusters

class ServiceInfo:
    def __init__(self, app: str, group: str, health_check_mode: str, metadata: Dict[str, str], name: str, protect_threshold: float, selector: 'ServiceSelector'):
        self.app = app
        self.group = group
        self.health_check_mode = health_check_mode
        self.metadata = metadata
        self.name = name
        self.protect_threshold = protect_threshold
        self.selector = selector

class ServiceSelector:
    def __init__(self, selector: str):
        self.selector = selector

class Cluster:
    def __init__(self, service_name: str, name: str, healthy_checker: 'ClusterHealthChecker', default_port: int, default_check_port: int, use_ip_port4_check: bool, metadata: Dict[str, str]):
        self.service_name = service_name
        self.name = name
        self.healthy_checker = healthy_checker
        self.default_port = default_port
        self.default_check_port = default_check_port
        self.use_ip_port4_check = use_ip_port4_check
        self.metadata = metadata

class ClusterHealthChecker:
    def __init__(self, type_: str):
        self.type = type_

class BeatInfo:
    def __init__(self, ip: str, port: int, weight: float, service_name: str, cluster: str, metadata: Dict[str, str], scheduled: bool, period: time.timedelta, state: int):
        self.ip = ip
        self.port = port
        self.weight = weight
        self.service_name = service_name
        self.cluster = cluster
        self.metadata = metadata
        self.scheduled = scheduled
        self.period = period
        self.state = state

class ExpressionSelector:
    def __init__(self, type_: str, expression: str):
        self.type = type_
        self.expression = expression

class ServiceList:
    def __init__(self, count: int, doms: List[str]):
        self.count = count
        self.doms = doms