import asyncio
import base64
import hashlib
import hmac
import logging
import uuid
from typing import Callable

from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, SERVER_ERROR, CLIENT_OVER_THRESHOLD
from v2.nacos.config.cache.config_info_cache import ConfigInfoCache
from v2.nacos.config.cache.config_subscribe_manager import ConfigSubscribeManager
from v2.nacos.config.filter.config_filter import ConfigFilterChainManager
from v2.nacos.config.model.config import ConfigListenContext
from v2.nacos.config.model.config_param import ConfigParam
from v2.nacos.config.model.config_request import AbstractConfigRequest, ConfigQueryRequest, \
    CONFIG_CHANGE_NOTIFY_REQUEST_TYPE, ConfigPublishRequest, ConfigRemoveRequest, ConfigBatchListenRequest
from v2.nacos.config.model.config_response import ConfigQueryResponse, ConfigPublishResponse, ConfigRemoveResponse, \
    ConfigChangeBatchListenResponse
from v2.nacos.config.remote.config_change_notify_request_handler import ConfigChangeNotifyRequestHandler
from v2.nacos.config.remote.config_grpc_connection_event_listener import ConfigGrpcConnectionEventListener
from v2.nacos.config.util.config_client_util import get_config_cache_key
from v2.nacos.transport.http_agent import HttpAgent
from v2.nacos.transport.nacos_server_connector import NacosServerConnector
from v2.nacos.transport.rpc_client import ConnectionType, RpcClient
from v2.nacos.transport.rpc_client_factory import RpcClientFactory
from v2.nacos.utils.common_util import get_current_time_millis
from v2.nacos.utils.md5_util import md5


class ConfigGRPCClientProxy:
    def __init__(self,
                 client_config: ClientConfig,
                 http_agent: HttpAgent,
                 config_info_cache: ConfigInfoCache,
                 config_filter_chain_manager: ConfigFilterChainManager):
        self.logger = logging.getLogger(Constants.CONFIG_MODULE)
        self.client_config = client_config
        self.namespace_id = client_config.namespace_id
        self.nacos_server_connector = NacosServerConnector(self.logger, self.client_config, http_agent)
        self.config_info_cache = config_info_cache
        self.uuid = uuid.uuid4()
        self.app_name = self.client_config.app_name if self.client_config.app_name else "unknown"
        self.rpc_client_manager = RpcClientFactory(self.logger)
        self.execute_config_listen_channel = asyncio.Queue()
        self.stop_event = asyncio.Event()
        self.listen_task = asyncio.create_task(self._execute_config_listen_task())
        self.last_all_sync_time = get_current_time_millis()
        self.config_subscribe_manager = ConfigSubscribeManager(self.logger, config_info_cache,
                                                               self.namespace_id,
                                                               config_filter_chain_manager,
                                                               self.execute_config_listen_channel)

    async def start(self):
        await self.nacos_server_connector.init()
        await self.fetch_rpc_client(0)

    async def fetch_rpc_client(self, task_id: int = 0) -> RpcClient:
        labels = {
            Constants.LABEL_SOURCE: Constants.LABEL_SOURCE_SDK,
            Constants.LABEL_MODULE: Constants.CONFIG_MODULE,
            Constants.APP_NAME_HEADER: self.app_name,
            "taskId": str(task_id),
        }
        rpc_client = await self.rpc_client_manager.create_client(
            str(self.uuid) + "_config_" + str(task_id), ConnectionType.GRPC, labels,
            self.client_config, self.nacos_server_connector)
        if rpc_client.is_wait_initiated():
            await rpc_client.register_server_request_handler(CONFIG_CHANGE_NOTIFY_REQUEST_TYPE,
                                                             ConfigChangeNotifyRequestHandler(
                                                                 self.logger,
                                                                 self.config_subscribe_manager,
                                                                 rpc_client.name))
            await rpc_client.register_connection_listener(ConfigGrpcConnectionEventListener(
                self.logger,
                self.config_subscribe_manager,
                self.execute_config_listen_channel,
                rpc_client)
            )
            await rpc_client.start()
        return rpc_client

    async def request_config_server(self, rpc_client: RpcClient, request: AbstractConfigRequest, response_class):
        try:
            await self.nacos_server_connector.inject_security_info(request.get_headers())
            now = get_current_time_millis()
            request.put_all_headers({
                Constants.CLIENT_APPNAME_HEADER: self.app_name,
                Constants.CLIENT_REQUEST_TS_HEADER: str(now),
                Constants.CLIENT_REQUEST_TOKEN_HEADER: md5(str(now) + self.client_config.app_key),
                Constants.EX_CONFIG_INFO: "true",
                Constants.CHARSET_KEY: "utf-8",
                'Timestamp': str(now),
            })

            credentials = self.client_config.credentials_provider.get_credentials()
            if credentials.get_access_key_id() and credentials.get_access_key_secret():
                if request.tenant:
                    resource = request.tenant + "+" + request.group
                else:
                    resource = request.group

                if resource.strip():
                    sign_str = f"{resource}+{now}"
                else:
                    sign_str = str(now)

                request.put_all_headers({
                    'Spas-AccessKey': credentials.get_access_key_id(),
                    'Spas-Signature': base64.encodebytes(
                        hmac.new(credentials.get_access_key_secret().encode(), sign_str.encode(),
                                 digestmod=hashlib.sha1).digest()).decode().strip(),
                })
                if credentials.get_security_token():
                    request.put_header("Spas-SecurityToken", credentials.get_security_token())

            response = await rpc_client.request(request, self.client_config.grpc_config.grpc_timeout)
            if response.get_result_code() != 200:
                raise NacosException(response.get_error_code(), response.get_message())
            if issubclass(response.__class__, response_class):
                return response
            else:
                raise NacosException(SERVER_ERROR, " Server return invalid response")
        except NacosException as e:
            self.logger.error("failed to invoke nacos config server : " + str(e))
            raise e
        except Exception as e:
            self.logger.error("failed to invoke nacos config server : " + str(e))
            raise NacosException(SERVER_ERROR, "Request nacos config server failed: " + str(e))

    async def query_config(self, data_id: str, group: str):
        self.logger.info("query config group:%s,dataId:%s,namespace:%s", group, data_id,
                         self.namespace_id)

        request = ConfigQueryRequest(
            group=group,
            dataId=data_id,
            tenant=self.namespace_id)
        request.put_header("notify", str(False))

        cache_key = get_config_cache_key(data_id, group, self.namespace_id)
        try:
            response = await self.request_config_server(await self.fetch_rpc_client(), request, ConfigQueryResponse)

            await self.config_info_cache.write_config_to_cache(cache_key, response.content,
                                                               response.encryptedDataKey)
            return response.content, response.encryptedDataKey
        except NacosException as e:
            if e.error_code == 300:
                await self.config_info_cache.write_config_to_cache(cache_key, "", "")
                return "", ""
            raise e

    async def publish_config(self, param: ConfigParam):
        self.logger.info("publish config group:%s,dataId:%s,content:%s,tag:%s", param.group, param.data_id,
                         param.content, param.tag)
        request = ConfigPublishRequest(
            group=param.group,
            dataId=param.data_id,
            tenant=self.namespace_id,
            content=param.content,
            casMd5=param.cas_md5)

        request.additionMap["tag"] = param.tag
        request.additionMap["appName"] = param.app_name
        request.additionMap["betaIps"] = param.beta_ips
        request.additionMap["type"] = param.type
        request.additionMap["src_user"] = param.src_user
        request.additionMap["encryptedDataKey"] = param.encrypted_data_key if param.encrypted_data_key else ""

        response = await self.request_config_server(await self.fetch_rpc_client(), request, ConfigPublishResponse)
        return response.is_success()

    async def remove_config(self, group: str, data_id: str):
        self.logger.info("remove config group:%s,dataId:%s", group, data_id)
        request = ConfigRemoveRequest(group=group,
                                      dataId=data_id,
                                      tenant=self.namespace_id)

        response = await self.request_config_server(await self.fetch_rpc_client(), request, ConfigRemoveResponse)
        return response.is_success()

    async def add_listener(self, data_id: str, group: str, listener: Callable) -> None:
        self.logger.info(f"add config listener,dataId:{data_id},group:{group}")
        await self.config_subscribe_manager.add_listener(data_id, group, self.namespace_id, listener)

    async def remove_listener(self, data_id: str, group: str, listener: Callable):
        self.logger.info(f"remove config listener,dataId:{data_id},group:{group}")
        await self.config_subscribe_manager.remove_listener(data_id, group, self.namespace_id, listener)

    async def _execute_config_listen_task(self):
        while not self.stop_event.is_set():
            try:
                await asyncio.wait_for(self.execute_config_listen_channel.get(), timeout=5)
            except asyncio.TimeoutError:
                self.logger.debug("Timeout occurred")
            except asyncio.CancelledError:
                return
            
            has_changed_keys = False
            is_sync_all = (get_current_time_millis() - self.last_all_sync_time) >= 5 * 60 * 1000
            listen_task_map = await self.config_subscribe_manager.execute_listener_and_build_tasks(is_sync_all)
            if len(listen_task_map) == 0:
                continue

            for task_id, cache_data_list in listen_task_map.items():
                if len(cache_data_list) == 0:
                    continue
                request = ConfigBatchListenRequest(group='', dataId='', tenant='')
                for cache_data in cache_data_list:
                    config_listen_context = ConfigListenContext(group=cache_data.group,
                                                                md5=cache_data.md5,
                                                                dataId=cache_data.data_id,
                                                                tenant=cache_data.tenant)
                    request.configListenContexts.append(config_listen_context)
                try:
                    rpc_client = await self.fetch_rpc_client(task_id)
                    response: ConfigChangeBatchListenResponse = await self.request_config_server(
                        rpc_client, request, ConfigChangeBatchListenResponse)

                    if len(response.changedConfigs) > 0:
                        has_changed_keys = True

                    for config_ctx in response.changedConfigs:
                        change_key = get_config_cache_key(config_ctx.dataId, config_ctx.group, config_ctx.tenant)
                        try:
                            content, encrypted_data_key = await self.query_config(config_ctx.dataId,
                                                                                  config_ctx.group)
                            await self.config_subscribe_manager.update_subscribe_cache(config_ctx.dataId,
                                                                                       config_ctx.group,
                                                                                       self.namespace_id,
                                                                                       content,
                                                                                       encrypted_data_key)
                        except Exception as e:
                            self.logger.error(f"failed to refresh config:{change_key},error:{str(e)}")
                            continue
                except Exception as e:
                    self.logger.error(f"failed to batch listen config ,error:{str(e)}")
                    continue

            if is_sync_all:
                self.last_all_sync_time = get_current_time_millis()

            if has_changed_keys:
                await self.execute_config_listen_channel.put(None)

    async def server_health(self):
        return (await self.fetch_rpc_client()).is_running()

    async def close_client(self):
        self.logger.info("close Nacos python config grpc client...")
        self.stop_event.set()
        await self.listen_task
        await self.rpc_client_manager.shutdown_all_clients()
