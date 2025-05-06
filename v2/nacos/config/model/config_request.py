from abc import ABC, abstractmethod
from typing import Optional, List, Dict

from v2.nacos.config.model.config import ConfigListenContext
from v2.nacos.transport.model.rpc_request import Request

CONFIG_CHANGE_NOTIFY_REQUEST_TYPE = "ConfigChangeNotifyRequest"


class AbstractConfigRequest(Request, ABC):
    group: Optional[str]
    dataId: Optional[str]
    tenant: Optional[str] = ''

    def get_module(self):
        return "config"

    def get_request_type(self) -> str:
        """
        提供一个默认实现或抛出NotImplementedError，明确指示子类需要覆盖此方法。
        """
        raise NotImplementedError("Subclasses should implement this method.")


class ConfigBatchListenRequest(AbstractConfigRequest):
    listen: bool = True
    configListenContexts: List[ConfigListenContext] = []

    def get_request_type(self):
        return "ConfigBatchListenRequest"


class ConfigChangeNotifyRequest(AbstractConfigRequest):

    def get_request_type(self):
        return "ConfigChangeNotifyRequest"


class ConfigQueryRequest(AbstractConfigRequest):
    tag: Optional[str] = ''

    def get_request_type(self):
        return "ConfigQueryRequest"


class ConfigPublishRequest(AbstractConfigRequest):
    content: Optional[str]
    casMd5: Optional[str]
    additionMap: Dict[str, str] = {}

    def get_request_type(self):
        return "ConfigPublishRequest"


class ConfigRemoveRequest(AbstractConfigRequest):

    def get_request_type(self):
        return "ConfigRemoveRequest"
