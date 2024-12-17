from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel


class Listener(ABC):

    @abstractmethod
    def listen(self, namespace: str, group: str, data_id: str, content: str):
        raise NotImplementedError("Subclasses should implement this method.")


class UsageType(Enum):
    request_type = "RequestType"
    response_type = "ResponseType"


class SearchConfigParam(BaseModel):
    search: str = ''
    dataId: str = ''
    group: str = ''
    tag: str = ''
    appName: str = ''
    pageNo: int = 0
    pageSize: int = 0


class ConfigParam(BaseModel):
    data_id: str = ''
    group: str = ''
    content: str = ''
    tag: str = ''
    app_name: str = ''
    beta_ips: str = ''
    cas_md5: str = ''
    type: str = ''
    src_user: str = ''
    encrypted_data_key: str = ''
    kms_key_id: str = ''
    usage_type: str = ''


class HandlerParam(BaseModel):
    data_id: str = ''
    content: str = ''
    encrypted_data_key: str = ''
    plain_data_key: str = ''
    key_id: str = ''
