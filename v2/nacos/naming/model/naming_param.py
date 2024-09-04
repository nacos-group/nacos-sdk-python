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
