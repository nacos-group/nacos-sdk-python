from typing import List, Callable

from v2.nacos.common.constants import Constants


class RegisterInstanceRequest:
    def __init__(self, service_name: str, ip: str, port: int, cluster_name: str, metadata, enable: bool = True,
                 healthy: bool = True,
                 ephemeral: bool = False, weight: float = 1.0, group_name: str = Constants.DEFAULT_GROUP):
        self.service_name = service_name
        self.ip = ip
        self.port = port
        self.cluster_name = cluster_name
        self.metadata = metadata if metadata else {}
        self.weight = weight
        self.enable = enable
        self.healthy = healthy
        self.group_name = group_name
        self.ephemeral = ephemeral


class BatchRegisterInstanceRequest:
    def __init__(self, service_name: str, instances: List[RegisterInstanceRequest],
                 group_name: str = Constants.DEFAULT_GROUP):
        self.service_name = service_name
        self.group_name = group_name
        self.instances = instances


class DeregisterInstanceRequest:
    def __init__(self, service_name: str, ip: str, port: int, cluster_name: str = "",
                 group_name: str = Constants.DEFAULT_GROUP,
                 ephemeral: bool = False):
        self.ip = ip
        self.port = port
        self.cluster_name = cluster_name
        self.service_name = service_name
        self.group_name = group_name
        self.ephemeral = ephemeral


class UpdateInstanceRequest(RegisterInstanceRequest):
    pass


class GetServiceParam:
    def __init__(self, service_name: str, clusters: List[str] = None, group_name: str = "DEFAULT_GROUP"):
        self.service_name = service_name
        self.clusters = clusters if clusters else []
        self.group_name = group_name


class GetAllServiceInfoParam:
    def __init__(self, name_space: str = "public", group_name: str = "DEFAULT_GROUP", page_no: int = 1,
                 page_size: int = 10):
        self.name_space = name_space
        self.group_name = group_name
        self.page_no = page_no
        self.page_size = page_size


class SubscribeParam:
    def __init__(self, service_name: str, subscribe_callback: Callable[[List[object], Exception], None],
                 clusters: List[str] = None, group_name: str = "DEFAULT_GROUP"):
        self.service_name = service_name
        self.clusters = clusters if clusters else []
        self.group_name = group_name
        self.subscribe_callback = subscribe_callback


class SelectAllInstancesParam(GetServiceParam):
    # Inherits from GetServiceParam and no new methods are needed
    pass


class SelectInstancesParam(SelectAllInstancesParam):
    def __init__(self, service_name: str, healthy_only: bool, clusters: List[str] = None,
                 group_name: str = "DEFAULT_GROUP"):
        super().__init__(service_name, clusters, group_name)
        self.healthy_only = healthy_only


class SelectOneHealthInstanceParam(SelectAllInstancesParam):
    # Inherits from SelectAllInstancesParam and no new methods are needed
    pass
