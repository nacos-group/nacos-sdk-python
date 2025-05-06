from typing import Optional, List

from pydantic import BaseModel

from v2.nacos.transport.model.rpc_response import Response


class ConfigContext(BaseModel):
    group: str = ''
    dataId: str = ''
    tenant: str = ''


class ConfigChangeBatchListenResponse(Response):
    changedConfigs: List[ConfigContext] = []

    def get_response_type(self) -> str:
        return "ConfigChangeBatchListenResponse"


class ConfigQueryResponse(Response):
    content: Optional[str] = ''
    encryptedDataKey: Optional[str] = ''
    contentType: Optional[str] = ''
    md5: Optional[str] = ''
    lastModified: Optional[int] = ''
    isBeta: bool = False
    tag: bool = False

    def get_response_type(self) -> str:
        return "ConfigQueryResponse"


class ConfigPublishResponse(Response):

    def get_response_type(self) -> str:
        return "ConfigPublishResponse"


class ConfigRemoveResponse(Response):

    def get_response_type(self) -> str:
        return "ConfigRemoveResponse"
