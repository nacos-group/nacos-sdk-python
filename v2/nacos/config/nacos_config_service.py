import logging

from v2.nacos.common.constants import Constants
from v2.nacos.config.filter_impl.config_filter_chain_manager import ConfigFilterChainManager
from v2.nacos.config.filter_impl.config_request import ConfigRequest
from v2.nacos.config.filter_impl.config_response import ConfigResponse
from v2.nacos.config.ilistener import Listener
from v2.nacos.config.impl.client_worker import ClientWorker
from v2.nacos.config.impl.local_config_info_processor import LocalConfigInfoProcessor
from v2.nacos.config.impl.local_encrypted_data_key_processor import LocalEncryptedDataKeyProcessor
from v2.nacos.config.impl.server_list_manager import ServerListManager
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.property_key_constants import PropertyKeyConstants
from v2.nacos.utils.param_utils import ParamUtils
from v2.nacos.utils.validator_utils import ValidatorUtils


class NacosConfigService:
    UP = "UP"

    DOWN = "DOWN"

    def __init__(self, logger, properties: dict):
        ValidatorUtils.check_init_param(properties)

        self.logger = logger
        self.namespace = properties.get(PropertyKeyConstants.NAMESPACE, None)
        if not self.namespace:
            self.namespace = ""

        self.config_filter_chain_manager = ConfigFilterChainManager()
        server_list_manager = ServerListManager(logger, properties)
        server_list_manager.start()
        self.worker = ClientWorker(logger, self.config_filter_chain_manager, server_list_manager, properties)
        self.local_config_info_processor = LocalConfigInfoProcessor(logger)
        self.local_encrypted_data_key_processor = LocalEncryptedDataKeyProcessor(logger)

    def get_config(self, data_id: str, group: str, timeout_ms: int) -> str:
        return self.__get_config_inner(self.namespace, data_id, group, timeout_ms)

    def get_config_and_sign_listener(self, data_id: str, group: str, timeout_ms: int, listener: Listener) -> str:
        content = self.get_config(data_id, group, timeout_ms)
        self.worker.add_tenant_listeners_with_content(data_id, group, content, [listener])
        return content

    def add_listener(self, data_id: str, group: str, listener: Listener) -> None:
        self.worker.add_tenant_listeners(data_id, group, [listener])

    def publish_config(self, data_id: str, group: str, content: str, config_type: str) -> bool:
        return self.__publish_config_inner(self.namespace, data_id, group, None, None, None, content, config_type, None)

    def publish_config_cas(self, data_id: str, group: str, content: str, cas_md5: str, config_type: str) -> bool:
        return self.__publish_config_inner(
            self.namespace, data_id, group, None, None, None, content, config_type, cas_md5
        )

    def remove_config(self, data_id: str, group: str) -> bool:
        return self.__remove_config_inner(self.namespace, data_id, group, None)

    def remove_listener(self, data_id: str, group: str, listener: Listener) -> None:
        self.worker.remove_tenant_listener(data_id, group, listener)

    def get_server_status(self) -> str:
        if self.worker.is_health_server():
            return NacosConfigService.UP
        else:
            return NacosConfigService.DOWN

    def shutdown(self) -> None:
        self.logger.info("%s do shutdown begin" % self.__class__.__name__)
        self.worker.shutdown()
        self.logger.info("%s do shutdown stop" % self.__class__.__name__)

    @staticmethod
    def __blank_2_default_group(group: str) -> str:
        if not group or not group.strip():
            return Constants.DEFAULT_GROUP
        else:
            return group.strip()

    def __get_config_inner(self, tenant: str, data_id: str, group: str, timeout_ms: int) -> str:
        group = self.__blank_2_default_group(group)
        ParamUtils.check_key_param(data_id, group)
        config_response = ConfigResponse()
        config_response.set_data_id(data_id)
        config_response.set_tenant(tenant)
        config_response.set_group(group)

        # use local config first
        content = self.local_config_info_processor.get_failover(self.worker.get_agent_name(), data_id, group, tenant)
        if content:
            pass

        try:
            response = self.worker.get_server_config(data_id, group, tenant, timeout_ms, False)
            config_response.set_content(response.get_content())
            config_response.set_encrypted_data_key(response.get_encrypted_data_key())
            self.config_filter_chain_manager.do_filter(None, config_response)
            content = config_response.get_content()
            return content
        except NacosException as e:
            self.logger.warning("[%s] [get-config] get from server error, dataId=%s, group=%s, tenant=%s, msg=%s"
                                 % (self.worker.get_agent_name(), data_id, group, tenant, str(e))
                                 )

        content_truncated = content[:100] + "..." if content and len(content) > 100 else content
        self.logger.warning("[%s] [get-config] get snapshot ok, dataId=%s, group=%s, tenant=%s, config=%s"
                            % (self.worker.get_agent_name(), data_id, group, tenant, content_truncated))
        content = self.local_config_info_processor.get_snapshot(self.worker.get_agent_name(), data_id, group, tenant)
        config_response.set_content(content)
        encrypted_data_key = self.local_encrypted_data_key_processor.get_encrypt_data_key_failover(
            self.worker.get_agent_name(), data_id, group, tenant
        )
        config_response.set_encrypted_data_key(encrypted_data_key)
        self.config_filter_chain_manager.do_filter(None, config_response)
        content = config_response.get_content()
        return content

    def __remove_config_inner(self, tenant, data_id, group, tag) -> bool:
        group = self.__blank_2_default_group(group)
        ParamUtils.check_key_param(data_id, group)
        return self.worker.remove_config(data_id, group, tenant, tag)

    def __publish_config_inner(
            self, tenant, data_id, group, tag, app_name, beta_ips, content,
            config_type, cas_md5
    ) -> bool:
        group = self.__blank_2_default_group(group)
        ParamUtils.check_key_param(data_id, group)

        config_request = ConfigRequest()
        config_request.set_data_id(data_id)
        config_request.set_tenant(tenant)
        config_request.set_group(group)
        config_request.set_content(content)
        config_request.set_type(config_type)
        self.config_filter_chain_manager.do_filter(config_request, None)
        content = config_request.get_content()
        encrypted_data_key = str(config_request.get_parameter("encryptedDataKey"))

        return self.worker.publish_config(
            data_id, group, tenant, app_name, tag, beta_ips, content, encrypted_data_key, cas_md5, config_type
        )



