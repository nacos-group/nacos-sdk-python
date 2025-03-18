import asyncio
import copy
import time
from typing import Callable

from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.config.cache.config_info_cache import ConfigInfoCache
from v2.nacos.config.filter.config_encryption_filter import ConfigEncryptionFilter
from v2.nacos.config.filter.config_filter import ConfigFilterChainManager
from v2.nacos.config.model.config_param import UsageType, ConfigParam
from v2.nacos.config.remote.config_grpc_client_proxy import ConfigGRPCClientProxy
from v2.nacos.nacos_client import NacosClient


class NacosConfigService(NacosClient):
    def __init__(self, client_config: ClientConfig):
        super().__init__(client_config, Constants.CONFIG_MODULE)
        self.lock = asyncio.Lock()
        self.config_filter_chain_manager = ConfigFilterChainManager()
        self.namespace_id = client_config.namespace_id
        self.config_info_cache = ConfigInfoCache(client_config)
        self.last_all_sync_time = time.time()
        self.grpc_client_proxy = ConfigGRPCClientProxy(client_config, self.http_agent, self.config_info_cache,
                                                       self.config_filter_chain_manager)

        if client_config.kms_config and client_config.kms_config.enabled:
            config_encryption_filter = ConfigEncryptionFilter(client_config)
            self.config_filter_chain_manager.add_filter(config_encryption_filter)
            self.logger.info("config encryption filter initialized")

    @staticmethod
    async def create_config_service(client_config: ClientConfig):
        config_service = NacosConfigService(client_config)
        await config_service.grpc_client_proxy.start()
        return config_service

    async def get_config(self, param: ConfigParam) -> str:
        if not param.data_id or not param.data_id.strip():
            raise NacosException(INVALID_PARAM, "data_id can not be empty")

        if not param.group:
            param.group = Constants.DEFAULT_GROUP

        content, encrypted_data_key = await self.config_info_cache.get_fail_over_config_cache(param.data_id,
                                                                                              param.group)
        if not content:
            try:
                content, encrypted_data_key = await self.grpc_client_proxy.query_config(param.data_id, param.group)
            except NacosException as e:
                if e.error_code == 400:
                    if self.client_config.disable_use_config_cache:
                        self.logger.warning(
                            "failed to get config from server,and is not allowed to read local cache,error:%s",
                            str(e))
                        raise e
                    return await self.config_info_cache.get_config_cache(param.data_id, param.group)
                raise e

        deep_copy_param = copy.deepcopy(param)
        deep_copy_param.encrypted_data_key = encrypted_data_key
        deep_copy_param.content = content
        deep_copy_param.usage_type = UsageType.response_type.value
        self.config_filter_chain_manager.do_filters(deep_copy_param)
        return deep_copy_param.content

    async def publish_config(self, param: ConfigParam) -> bool:
        if not param.data_id or not param.data_id.strip():
            raise NacosException(INVALID_PARAM, "data_id can not be empty")

        if not param.content or not param.content.strip():
            raise NacosException(INVALID_PARAM, "config content can not be empty")

        if not param.group:
            param.group = Constants.DEFAULT_GROUP

        param.usage_type = UsageType.request_type.value

        self.config_filter_chain_manager.do_filters(param)

        return await self.grpc_client_proxy.publish_config(param)

    async def remove_config(self, param: ConfigParam):
        if not param.data_id or not param.data_id.strip():
            raise NacosException(INVALID_PARAM, "data_id can not be empty")

        if not param.group:
            param.group = Constants.DEFAULT_GROUP

        return await self.grpc_client_proxy.remove_config(param.group, param.data_id)

    async def add_listener(self, data_id: str, group: str, listener: Callable) -> None:
        if not data_id or not data_id.strip():
            raise NacosException(INVALID_PARAM, "data_id can not be empty")

        if not group:
            group = Constants.DEFAULT_GROUP

        if listener is None:
            raise NacosException(INVALID_PARAM, "config listener can not be null")

        return await self.grpc_client_proxy.add_listener(data_id, group, listener)

    async def remove_listener(self, data_id: str, group: str, listener: Callable):
        if not data_id or not data_id.strip():
            raise NacosException(INVALID_PARAM, "data_id can not be empty")

        if not group:
            group = Constants.DEFAULT_GROUP

        if listener is None:
            raise NacosException(INVALID_PARAM, "config listener can not be null")

        return await self.grpc_client_proxy.remove_listener(data_id, group, listener)

    async def server_health(self) -> bool:
        return await self.grpc_client_proxy.server_health()

    async def shutdown(self):
        """关闭资源服务"""
        await self.grpc_client_proxy.close_client()
