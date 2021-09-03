import hashlib
from typing import Optional

from v2.nacos.common.constants import Constants
from v2.nacos.config.ilistener import Listener
from v2.nacos.config.impl.local_config_info_processor import LocalConfigInfoProcessor
from v2.nacos.exception.nacos_exception import NacosException


class CacheData:
    def __init__(self, logger, config_filter_chain_manager, name, data_id, group, tenant):
        if not data_id or not group:
            raise NacosException("[ArgumentNullException]dataId="+data_id+ ", group=" + group)

        self.logger = logger
        self.name = name
        self.config_filter_chain_manager = config_filter_chain_manager
        self.data_id = data_id
        self.group = group
        self.tenant = tenant
        self.listeners = []
        self.is_initializing = True
        self.content = self.__load_cache_content_from_disk_local(name, data_id, group, tenant)
        self.md5 = self.get_md5_str(self.content)

        self.is_use_local_config = False
        self.local_config_last_modified = None

    def check_listener_md5(self) -> None:
        for wrap in self.listeners:
            if wrap.last_call_md5 != self.md5:
                self.__safe_notify_listener(self.content, self.md5, wrap)

    @staticmethod
    def __safe_notify_listener(content: str, md5: str, wrap) -> None:
        listener = wrap.listener
        wrap.last_content = content
        wrap.last_call_md5 = md5
        listener.receive_config_info(content)

    def add_listener(self, listener) -> None:
        if not listener:
            raise NacosException("[ArgumentException]Listener is None")
        wrap = CacheData.ManagerListenerWrap(listener=listener, md5=self.md5, last_content=self.content)
        self.listeners.append(wrap)

    def remove_listener(self, listener) -> None:
        if not listener:
            raise NacosException("[ArgumentException]Listener is None")
        wrap = CacheData.ManagerListenerWrap(listener=listener)
        try:
            self.listeners.remove(wrap)
            self.logger.info("[%s][remove-listener] ok, dataId=%s, group=%s, cnt=%s"
                             % (self.name, self.data_id, self.group, len(self.listeners)))
        except NacosException as e:
            pass

    def set_use_local_config_info(self, use_local_config_info: bool) -> None:
        self.is_use_local_config = use_local_config_info
        if not use_local_config_info:
            self.local_config_last_modified = -1

    def set_local_config_info_version(self, local_config_last_modified: int) -> None:
        self.local_config_last_modified = local_config_last_modified

    def get_local_config_info_version(self) -> int:
        return self.local_config_last_modified

    def set_content(self, content: str) -> None:
        self.content = content
        self.md5 = self.get_md5_str(content)

    @staticmethod
    def get_md5_str(config: str) -> str:
        if not config:
            return Constants.NULL
        else:
            md5 = hashlib.md5()
            md5.update(config)
            return md5.hexdigest()

    def get_hash_code(self) -> int:
        prime = 31
        result = 1
        result = prime * result
        result += 0 if not self.data_id else hash(self.data_id)
        result += 0 if not self.group else hash(self.group)
        return result

    def get_listeners(self) -> list:
        result = []
        for wrap in self.listeners:
            result.append(wrap.listener)
        return result

    @staticmethod
    def __load_cache_content_from_disk_local(name: str, data_id: str, group: str, tenant: str) -> str:
        content = LocalConfigInfoProcessor.get_failover(name, data_id, group, tenant)
        if not content:
            content = LocalConfigInfoProcessor.get_snapshot(name, data_id, group, tenant)
        return content

    class ManagerListenerWrap:
        def __init__(self, listener=None, md5=None, last_content=None):
            self.listener = listener
            self.last_call_md5 = md5
            self.last_content = last_content
