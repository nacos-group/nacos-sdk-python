from typing import List, Callable, Optional

from v2.nacos.common.constants import Constants
from pydantic import BaseModel


class RegisterInstanceRequest(BaseModel):
    instance_id: Optional[str]
    ip: str
    port: int
    weight: float = 1.0
    healthy: bool = True
    enable: bool = True
    ephemeral: bool = True
    cluster_name: str
    serviceName: str
    groupName: str = Constants.DEFAULT_GROUP
    metadata: dict = {}


class BatchRegisterInstanceRequest(BaseModel):
    service_name: str
    instances: List[RegisterInstanceRequest]
    group_name: str = Constants.DEFAULT_GROUP


class DeregisterInstanceRequest(BaseModel):
    ip: str
    port: int
    cluster_name: str
    service_name: str
    group_name: str = Constants.DEFAULT_GROUP
    ephemeral: bool = True


class UpdateInstanceRequest(RegisterInstanceRequest):
    pass


class ExpressionSelector(BaseModel):
    type: str
    expression: str


class GetServiceRequest(BaseModel):
    service_name: str
    group_name: str = Constants.DEFAULT_GROUP
    clusters: List[str] = []


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
