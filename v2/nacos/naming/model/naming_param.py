from pydantic import BaseModel

from v2.nacos.common.constants import Constants


class RegisterInstanceParam(BaseModel):
    ip: str
    port: int
    weight: float = 1.0
    enabled: bool = True
    healthy: bool = True
    metadata: dict[str, str] = {}
    cluster_name: str = ''
    service_name: str
    group_name: str = Constants.DEFAULT_GROUP
    ephemeral: bool = True


class BatchRegisterInstanceParam(BaseModel):
    service_name: str
    group_name: str = Constants.DEFAULT_GROUP
    instances: list[RegisterInstanceParam] = []


class DeregisterInstanceRequest(BaseModel):
    ip: str
    port: int
    cluster_name: str = ''
    service_name: str
    group_name: str = Constants.DEFAULT_GROUP
    ephemeral: bool = True


class ListInstanceRequest(BaseModel):
    service_name: str
    group_name: str = Constants.DEFAULT_GROUP
    clusters: list[str] = []
    subscribe: bool = True
    healthy_only: bool


class SubscribeServiceRequest(BaseModel):
    service_name: str
    group_name: str = Constants.DEFAULT_GROUP
    clusters: list[str] = []
