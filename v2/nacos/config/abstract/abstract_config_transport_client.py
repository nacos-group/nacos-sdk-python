import sched
import time
from abc import ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor

from v2.nacos.common.constants import Constants
from v2.nacos.config.filter_impl.config_response import ConfigResponse
from v2.nacos.config.impl.server_list_manager import ServerListManager
from v2.nacos.property_key_constants import PropertyKeyConstants
from v2.nacos.security.security_proxy import SecurityProxy


class AbstractConfigTransportClient(metaclass=ABCMeta):
    SECURITY_TOKEN_HEADER = "Spas-SecurityToken"

    ACCESS_KEY_HEADER = "Spas-AccessKey"

    CONFIG_INFO_HEADER = "exConfigInfo"

    DEFAULT_CONFIG_INFO = "true"

    def __init__(self, logger, properties: dict, server_list_manager: ServerListManager):
        self.logger = logger
        self.properties = properties
        self.server_list_manager = server_list_manager

        if PropertyKeyConstants.ENCODE in properties.keys():
            self.encode = properties[PropertyKeyConstants.ENCODE].strip()
        else:
            self.encode = Constants.ENCODE

        if PropertyKeyConstants.NAMESPACE in properties.keys():
            self.tenant = properties[PropertyKeyConstants.NAMESPACE]
        else:
            self.tenant = None

        self.security_proxy = SecurityProxy(logger, properties)

        self.__init_ak_sk(properties)

        self.executor = None
        self.max_retry = 3
        self.security_info_refresh_interval_second = 5
        self.access_key = None
        self.secret_key = None
        self.login_timer = None

    def _get_spas_headers(self):
        spas_header = {}
        # todo STS 临时凭证鉴权的优先级高于 AK/SK 鉴权
        return spas_header

    def _get_security_headers(self) -> dict:
        # todo
        access_token = self.security_proxy.get_access_token()
        if not access_token or not access_token.strip():
            return
        security_headers = {Constants.ACCESS_TOKEN: access_token}
        return security_headers

    def _get_common_header(self) -> dict:
        # todo
        return {}

    def get_access_token(self) -> str:
        return self.security_proxy.get_access_token()

    def __get_sts_credential(self) -> str:
        # todo
        pass

    def __get_sts_response(self) -> str:
        # todo
        pass

    def __init_ak_sk(self, properties: dict) -> None:
        # todo
        pass

    def set_executor(self, executor) -> None:
        self.executor = executor

    def start(self) -> None:
        if self.security_proxy.is_enabled():
            self.security_proxy.login_servers(self.server_list_manager.get_server_urls())

            self.login_timer = sched.scheduler(time.time, time.sleep)
            self.login_timer.enter(self.security_info_refresh_interval_second, 0, self.security_proxy.login_servers,
                                   (self.server_list_manager.get_server_urls(),))
            self.executor = ThreadPoolExecutor()
            self.executor.submit(self.login_timer.run)

        self.start_internal()

    @abstractmethod
    def start_internal(self) -> None:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    def get_encode(self) -> str:
        return self.encode

    def get_tenant(self) -> str:
        return self.tenant

    @abstractmethod
    def notify_listen_config(self) -> None:
        pass

    @abstractmethod
    def execute_config_listen(self) -> None:
        pass

    @abstractmethod
    def remove_cache(self, data_id: str, group: str) -> None:
        pass

    @abstractmethod
    def query_config(self, data_id: str, group: str, tenant: str, read_timeout: int, notify: bool) -> ConfigResponse:
        pass

    @abstractmethod
    def publish_config(self,
                       data_id: str, group: str, tenant: str, app_name: str,
                       tag: str, beta_ips: str, content: str, encrypted_data_key: str,
                       cas_md5: str, config_type: str
                       ) -> bool:
        pass

    @abstractmethod
    def remove_config(self, data_id: str, group: str, tenant: str, tag: str) -> bool:
        pass

    @abstractmethod
    def shutdown(self):
        pass
