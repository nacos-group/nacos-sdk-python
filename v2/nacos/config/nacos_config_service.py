import asyncio
import copy
import os
import time
from typing import List

from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM, INVALID_INTERFACE_ERROR
from v2.nacos.config.cache.config_cache import ConfigCache
from v2.nacos.config.filter.config_encryption_filter import ConfigEncryptionFilter
from v2.nacos.config.filter.config_filter import new_config_filter_chain_manager, \
    register_config_filter_to_chain
from v2.nacos.config.model import config
from v2.nacos.config.model import config_request, config_response
from v2.nacos.config.model.config import CacheDataListener
from v2.nacos.config.model.config_param import Listener
from v2.nacos.config.model.config_param import UsageType, ConfigParam
from v2.nacos.config.model.config_request import CONFIG_CHANGE_NOTIFY_REQUEST_TYPE
from v2.nacos.config.model.config_response import ConfigPublishResponse, \
    ConfigChangeBatchListenResponse, ConfigRemoveResponse
from v2.nacos.config.remote.config_change_notify_request_handler import ConfigChangeNotifyRequestHandler
from v2.nacos.config.remote.config_proxy import ConfigProxy
from v2.nacos.nacos_client import NacosClient
from v2.nacos.transport.model.rpc_response import Response
from v2.nacos.utils import common_util, md5_util, content_util


class CacheData:
    def __init__(self, is_initializing: bool, data_id: str, group: str, tenant: str, content: str, md5: str,
                 encrypted_data_key: str, task_id: int,
                 config_client, cache_data_listener: CacheDataListener, content_type: str = '',
                 is_sync_with_server: bool = False):
        self.is_initializing = is_initializing
        self.data_id = data_id
        self.group = group
        self.tenant = tenant
        self.content = content
        self.content_type = content_type
        self.md5 = md5
        self.cache_data_listener = cache_data_listener
        self.encrypted_data_key = encrypted_data_key
        self.task_id = task_id
        self.config_client = config_client
        self.is_sync_with_server = is_sync_with_server

    def execute_listener(self):
        self.cache_data_listener.last_md5 = self.md5
        cache_key = common_util.get_config_cache_key(self.data_id, self.group, self.tenant)
        self.config_client.cache_map[cache_key] = self

        param = ConfigParam(data_id=self.data_id, group=self.group, content=self.content,
                            encrypted_data_key=self.encrypted_data_key, usage_type=UsageType.response_type.value)
        self.config_client.config_filter_chain_manager.do_filters(param)
        decrypted_content = param.content
        self.cache_data_listener.listener.listen(self.tenant, self.group, self.data_id, decrypted_content)


class NacosConfigService(NacosClient):
    """配置服务接口，用于获取和监听配置信息，以及发布配置"""

    def __init__(self, client_config: ClientConfig):
        super().__init__(client_config, Constants.CONFIG_MODULE)
        self.lock = asyncio.Lock()
        self.config_filter_chain_manager = new_config_filter_chain_manager()
        self.namespace_id = client_config.namespace_id
        self.config_cache = ConfigCache(client_config)
        self.config_proxy = ConfigProxy(client_config, self.http_agent, self.config_cache)
        self.config_cache_dir = os.path.join(self.client_config.cache_dir, "config")
        self.listen_execute = asyncio.Queue()
        self.last_all_sync_time = time.time()
        self.cache_map = {}
        config_encryption_filter = ConfigEncryptionFilter(client_config)
        register_config_filter_to_chain(self.config_filter_chain_manager, config_encryption_filter)

    @staticmethod
    async def create_config_service(client_config: ClientConfig):

        config_service = NacosConfigService(client_config)
        await config_service.config_proxy.start()
        if config_service.config_proxy.rpc_client.is_wait_initiated():
            await config_service.config_proxy.rpc_client.register_server_request_handler(
                CONFIG_CHANGE_NOTIFY_REQUEST_TYPE, ConfigChangeNotifyRequestHandler(config_service)
            )
            config_service.config_proxy.rpc_client.tenant = config_service.config_proxy.client_config.namespace_id
            await config_service.config_proxy.rpc_client.start()

        asyncio.create_task(config_service.start_internal())
        return config_service

    async def get_config(self, param: ConfigParam):
        try:
            content, encrypted_data_key = await self._get_config_inner(param)

            deep_copy_param = copy.deepcopy(param)
            deep_copy_param.encrypted_data_key = encrypted_data_key
            deep_copy_param.content = content
            deep_copy_param.usage_type = UsageType.response_type.value
            self.config_filter_chain_manager.do_filters(deep_copy_param)
            return deep_copy_param.content
        except Exception as e:
            self.logger.error("[nacos_config_service.get_config] error: err: %s", str(e))
            raise

    async def _get_config_inner(self, param: ConfigParam):
        if not param.data_id:
            self.logger.error("[nacos_config_service._get_config_inner] data_id can not be empty")
            raise NacosException(INVALID_PARAM, "data_id can not be empty")
        if not param.group:
            param.group = Constants.DEFAULT_GROUP

        cache_key = self.config_cache.get_config_cache_key(param)
        content, encrypted_data_key = self.config_cache.load_failover_cache_from_disk(cache_key)
        if content:
            return content, encrypted_data_key
        try:
            response = await self.config_proxy.query_config(param.data_id, param.group, self.namespace_id, False)
            if response and not response.is_success():
                return response.content, response.encryptedDataKey
            encrypted_data_key = response.encryptedDataKey
            content = response.content
            return content, encrypted_data_key
        except Exception as e:
            self.logger.error(
                f"[nacos_config_service._get_config_inner] get config from server error, dataId:{param.data_id}, group:{param.group}, namespaceId:{self.namespace_id}, error:{str(e)}")
            if self.client_config.disable_use_snap_shot:
                self.logger.warning(
                    "[nacos_config_service._get_config_inner] get config from remote nacos server fail, and is not allowed to read local file, err:%s",
                    str(e))
                return "", ""
            try:
                is_cipher = param.data_id.startswith(Constants.CIPHER_PRE_FIX)
                return self.config_cache.load_cache_from_disk(cache_key, is_cipher)
            except Exception as e:
                self.logger.error(
                    "[nacos_config_service._get_config_inner] read config or encryptedDataKey from server and cache fail, err=%s, dataId=%s, group=%s, namespaceId=%s",
                    str(e), param.data_id, param.group, self.namespace_id)
                raise NacosException(INVALID_INTERFACE_ERROR,
                                     f"failed to qread config or encryptedDataKey from server and cache fail, error: {str(e)}")

    async def add_listener(self, param: ConfigParam, listener: Listener) -> None:
        """为指定的配置添加监听器，当服务器修改配置后，客户端将使用传入的监听器进行回调"""
        if not param.data_id:
            self.logger.error("[nacos_config_service.add_listener] data_id cannot be empty")
            raise NacosException(INVALID_PARAM, "data_id can not be empty")
        if not param.group:
            self.logger.error("[nacos_config_service.add_listener] group cannot be empty")
            raise NacosException(INVALID_PARAM, "group can not be empty")
        client_config = self.client_config
        if not client_config:
            self.logger.error("[nacos_config_service.add_listener] client_config cannot be empty")
            raise NacosException(INVALID_PARAM, "client_config cannot be empty")

        key = self.config_cache.get_config_cache_key(param)

        if key in self.cache_map:
            c_data = self.cache_map[key]
            c_data.is_initializing = True
        else:
            content, md5_str, encrypted_data_key = '', '', ''
            is_cipher = param.data_id.startswith(Constants.CIPHER_PRE_FIX)
            try:
                content, encrypted_data_key = self.config_cache.load_cache_from_disk(key, is_cipher)
                md5_str = md5_util.md5(content) if content else ''
            except Exception as e:
                self.logger.warning(f"[nacos_config_service.add_listener] cannot load cache from disk, error:{str(e)}")

            listener = CacheDataListener(listener, md5_str)

            cache_data = CacheData(
                is_initializing=True,
                data_id=param.data_id,
                group=param.group,
                tenant=self.namespace_id,
                content=content,
                md5=md5_str,
                cache_data_listener=listener,
                encrypted_data_key=encrypted_data_key,
                task_id=len(self.cache_map) // Constants.PER_TASK_CONFIG_SIZE,
                config_client=self
            )

            async with self.lock:
                self.cache_map[key] = cache_data

    async def publish_config(self, param: ConfigParam) -> bool:

        if not param.data_id:
            self.logger.error("[nacos_config_service.publish_config] data_id can not be empty")
            raise NacosException(INVALID_PARAM, "data_id can not be empty")

        if not param.content:
            self.logger.error("[nacos_config_service.publish_config] content can not be empty")
            raise NacosException(INVALID_PARAM, "content can not be empty")

        if not param.group:
            param.group = Constants.DEFAULT_GROUP

        param.usage_type = UsageType.request_type.value

        try:
            self.config_filter_chain_manager.do_filters(param)

            request = config_request.ConfigPublishRequest(
                group=param.group, dataId=param.data_id, tenant=self.namespace_id,
                content=param.content, casMd5=param.cas_md5)

            request.additionMap["tag"] = param.tag
            request.additionMap["appName"] = param.app_name
            request.additionMap["betaIps"] = param.beta_ips
            request.additionMap["type"] = param.type
            request.additionMap["src_user"] = param.src_user
            request.additionMap["encryptedDataKey"] = param.encrypted_data_key

            response = await self.config_proxy.request_proxy(request, ConfigPublishResponse)

            if response:
                return self._build_response(response, param)
        except Exception as e:
            self.logger.error(
                "[nacos_config_service.publish_config] error, dataId: %s, group: %s, tenant: %s, code: %s, err: %s",
                param.data_id, param.group, self.namespace_id, "unkown", str(e))
            return False

    async def remove_config(self, param: ConfigParam):
        """移除配置信息"""
        if not param.data_id:
            self.logger.error("[nacos_config_service.remove_config] data_id can not be empty")
            raise NacosException(INVALID_PARAM, "data_id can not be empty")

        if not param.group:
            param.group = Constants.DEFAULT_GROUP

        try:
            request = config_request.ConfigRemoveRequest(group=param.group, dataId=param.data_id,
                                                         tenant=self.namespace_id)

            response = await self.config_proxy.request_proxy(request, ConfigRemoveResponse)
            if response:
                return self._build_response(response, param)
            else:
                self.logger.error("Response is None")
                return False
        except Exception as e:
            return False

    async def remove_listener(self, param: ConfigParam):
        """移除指定的监听器"""
        if not self.client_config:
            self.logger.error("[nacos_config_service.remove_listener] get config info failed")
            raise NacosException(INVALID_PARAM, "get config info failed")
        try:
            async with self.lock:
                del self.cache_map[common_util.get_config_cache_key(param.data_id, param.group, self.namespace_id)]
            return True
        except Exception as e:
            return False

    async def close_client(self):
        """关闭资源服务"""
        await self.config_proxy.get_rpc_client().shutdown()

    def _build_response(self, response: Response, param: ConfigParam):
        if response.is_success():
            self.logger.info("[nacos_config_service._build_response] ok, dataId: %s, group: %s, tenant: %s, config: %s",
                             param.data_id, param.group, self.namespace_id,
                             content_util.truncate_content(param.content))
            return True
        err_msg = response.get_message()
        self.logger.error("[nacos_config_service._build_response] response has some err: %s", err_msg)
        return False

    async def start_internal(self):
        while True:
            try:
                await asyncio.wait_for(self.listen_execute.get(), timeout=Constants.EXECUTOR_ERR_DELAY)
            except Exception as e:
                self.logger.warning("[nacos_config_service.start_internal] warning, warning: %s", str(e))
            finally:
                try:
                    await asyncio.sleep(3)
                    await self.execute_config_listen()
                except Exception as e:
                    self.logger.error("[nacos_config_service.start_internal] error, err: %s", str(e))

    async def execute_config_listen(self):

        need_all_sync = (time.time() - self.last_all_sync_time) >= Constants.ALL_SYNC_INTERNAL
        has_changed_keys = False

        listen_task_map = self.build_listen_task(need_all_sync)
        if not listen_task_map:
            return

        for task_id, caches in listen_task_map.items():
            request = self.build_config_batch_listen_request(caches)
            try:
                response = await self.config_proxy.request_proxy(request, ConfigChangeBatchListenResponse)
                if response is None:
                    self.logger.warning(
                        "[nacos_config_service.execute_config_listen] ConfigBatchListenRequest failure, response is nil")
                    continue
                if not response.is_success():
                    self.logger.warning(
                        f"[nacos_config_service.execute_config_listen] ConfigBatchListenRequest failure, error code:{response.get_error_code()}")
                    continue

                if not isinstance(response, config_response.ConfigChangeBatchListenResponse):
                    continue

                if len(response.changedConfigs) > 0:
                    has_changed_keys = True

                change_keys = {}
                for v in response.changedConfigs:
                    change_key = common_util.get_config_cache_key(v["dataId"], v["group"], v["tenant"])
                    if change_key in self.cache_map:
                        c_data = self.cache_map[change_key]
                        await self.refresh_content_and_check(c_data, not c_data.is_initializing)

                for k, v in self.cache_map.items():
                    data = v
                    change_key = common_util.get_config_cache_key(data.data_id, data.group, data.tenant)
                    if change_key not in change_keys:
                        data.is_sync_with_server = True
                        async with self.lock:
                            self.cache_map[change_key] = data
                        continue

                    data.is_initializing = True
                    async with self.lock:
                        self.cache_map[change_key] = data

            except Exception as e:
                self.logger.warning(
                    f"[nacos_config_service.execute_config_listen] ConfigBatchListenRequest failure, err:{str(e)}")
                continue
            finally:
                if need_all_sync:
                    self.last_all_sync_time = time.time()

                if has_changed_keys:
                    self.async_notify_listen_config()

    def build_config_batch_listen_request(self, caches: List[CacheData]):
        request = config_request.ConfigBatchListenRequest(group='', dataId='', tenant='')
        for cache in caches:
            config_listen_context = config.ConfigListenContext(group=cache.group, md5=cache.md5, dataId=cache.data_id,
                                                               tenant=cache.tenant)
            request.configListenContexts.append(config_listen_context)
        return request

    async def refresh_content_and_check(self, cache_data: CacheData, notify: bool):
        try:
            config_query_response = await self.config_proxy.query_config(
                cache_data.data_id, cache_data.group, cache_data.tenant, notify)

            if config_query_response and not config_query_response.is_success():
                self.logger.error(
                    f"[nacos_config_service.refresh_content_and_check] refresh cached config from server error:{config_query_response.get_message()}, dataId={cache_data.data_id}, group={cache_data.group}")
                return

            cache_data.content = config_query_response.content
            cache_data.content_type = config_query_response.contentType
            cache_data.encrypted_data_key = config_query_response.encryptedDataKey
            if notify:
                self.logger.info(
                    f"[nacos_config_service.refresh_content_and_check] data-received, dataId={cache_data.data_id}, group={cache_data.group}, tenant={cache_data.tenant}, md5={cache_data.md5}, content={content_util.truncate_content(cache_data.content)}, type={cache_data.content_type}")

            cache_data.md5 = md5_util.md5(cache_data.content)
            if cache_data.md5 != cache_data.cache_data_listener.last_md5:
                cache_data.execute_listener()
        except Exception as e:
            self.logger.error(
                "[nacos_config_service.refresh_content_and_check] refresh content and check md5 fail, dataId=%s, group=%s, tenant=%s, error:%s",
                cache_data.data_id, cache_data.group, cache_data.tenant, str(e))

    def build_listen_task(self, need_all_sync: bool):
        listen_task_map = {}

        for data in self.cache_map.values():
            if not isinstance(data, CacheData):
                continue
            if data.is_sync_with_server:

                if data.md5 != data.cache_data_listener.last_md5:
                    data.execute_listener()
                if not need_all_sync:
                    continue
            if data.task_id not in listen_task_map:
                listen_task_map[data.task_id] = []
            listen_task_map[data.task_id].append(data)

        return listen_task_map

    def async_notify_listen_config(self):
        asyncio.create_task(self._set_listen_config())

    async def _set_listen_config(self):
        await self.listen_execute.put(None)
