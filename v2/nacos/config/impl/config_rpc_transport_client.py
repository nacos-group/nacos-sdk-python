import uuid
from queue import Queue

from v2.nacos.ability.client_abilities import ClientAbilities
from v2.nacos.common.constants import Constants
from v2.nacos.common.utils import get_current_time_millis
from v2.nacos.config.abstract.abstract_config_transport_client import AbstractConfigTransportClient
from v2.nacos.config.common.group_key import GroupKey
from v2.nacos.config.filter_impl.config_response import ConfigResponse
from v2.nacos.config.impl.config_rpc_server_request_handler import ConfigRpcServerRequestHandler
from v2.nacos.config.impl.local_config_info_processor import LocalConfigInfoProcessor
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.naming.core.server_list_manager import ServerListManager
from v2.nacos.remote.remote_constants import RemoteConstants
from v2.nacos.remote.requests import ConfigRemoveRequest, ConfigBatchListenRequest, ConfigPublishRequest, \
    ConfigQueryRequest
from v2.nacos.remote.requests.request import Request
from v2.nacos.remote.responses import ConfigQueryResponse
from v2.nacos.remote.rpc_client import RpcClient
from v2.nacos.remote.rpc_client_factory import RpcClientFactory
from v2.nacos.remote.utils import ConnectionType
from v2.nacos.utils.app_name_utils import AppNameUtils
from v2.nacos.utils.env_util import EnvUtil


class ConfigRpcTransportClient(AbstractConfigTransportClient):
    ALL_SYNC_INTERNAL = 5 * 60 * 1000

    RPC_AGENT_NAME = "config_rpc_client"

    def __init__(self, logger, properties: dict, server_list_manager: ServerListManager, cache_map: dict):
        super().__init__(logger, properties, server_list_manager)
        self.listen_execute_bell = Queue()
        self.bell_item = object()
        self.last_all_sync_time = get_current_time_millis()
        self.uuid = uuid.uuid4()
        self.cache_map = cache_map

    def start_internal(self) -> None:
        pass

    def get_name(self) -> str:
        return ConfigRpcTransportClient.RPC_AGENT_NAME

    def notify_listen_config(self) -> None:
        self.listen_execute_bell.put(self.bell_item)

    def execute_config_listen(self) -> None:
        listen_caches_map = {}
        remove_listen_caches_map = {}
        now = get_current_time_millis()
        need_all_sync = (now - self.last_all_sync_time) >= ConfigRpcTransportClient.ALL_SYNC_INTERNAL

        # todo cache
        for cache in self.cache_map.values():
            pass

        has_changed_keys = False

        if listen_caches_map:
            pass

        if remove_listen_caches_map:
            pass

        if need_all_sync:
            self.last_all_sync_time = now

        if has_changed_keys:
            self.notify_listen_config()

    def __ensure_rpc_client(self, task_id: str) -> RpcClient:
        labels = self.__get_labels()
        new_labels = labels.copy()
        new_labels["taskId"] = task_id

        client_name = "config-" + task_id + "-" + str(self.uuid)
        rpc_client = RpcClientFactory.create_client(client_name, ConnectionType.GRPC, new_labels)

        if rpc_client.is_wait_initiated():
            self.__init_rpc_client_handler(rpc_client)
            rpc_client.set_tenant(self.get_tenant())
            rpc_client.set_client_abilities(self.__init_abilities())
            rpc_client.start()

        return rpc_client

    @staticmethod
    def __init_abilities() -> ClientAbilities:
        client_abilities = ClientAbilities()
        client_abilities.get_remote_ability().set_support_remote_connection(True)
        client_abilities.get_config_ability().set_support_remote_metrics(True)
        return client_abilities

    @staticmethod
    def __build_config_request(caches: list) -> ConfigBatchListenRequest:
        config_change_listen_request = ConfigBatchListenRequest()
        for cache_data in caches:
            config_change_listen_request.add_config_listen_context(
                cache_data.group, cache_data.data_id, cache_data.tenant, cache_data.md5
            )
        return config_change_listen_request

    def remove_cache(self, data_id: str, group: str) -> None:
        # todo question?
        self.notify_listen_config()

    def __un_listen_config_change(self, rpc_client: RpcClient,
                                  config_change_listen_request: ConfigBatchListenRequest) -> bool:
        response = self.__request_proxy(rpc_client, config_change_listen_request)
        return response.is_success()

    def query_config(self, data_id: str, group: str, tenant: str, read_timeout: int, notify: bool) -> ConfigResponse:
        request = ConfigQueryRequest.build(data_id, group, tenant)
        request.put_header("notify", str(notify))
        rpc_client = self.get_one_running_client()

        response = self.__request_proxy(rpc_client, request, read_timeout)
        config_response = ConfigResponse()
        if response.is_success():
            LocalConfigInfoProcessor.save_snapshot(
                self.get_name(), data_id, group, tenant, response.get_content())
            config_response.set_content(response.get_content())
            if response.get_content_type():
                config_type = response.get_content_type()
            else:
                config_type = "text"

            config_response.set_config_type(config_type)
            encrypted_data_key = response.get_encrypted_data_key()
            # todo save snapshot
            return config_response
        elif response.get_error_code() == ConfigQueryResponse.CONFIG_QUERY_CONFLICT:
            self.logger.error(
                "[%s][sub-server-error] get server config being modified concurrently, dataId=%s, group=%s, tanant=%s"
                % (self.get_name(), data_id, group, tenant)
            )
            raise NacosException(str(NacosException.CONFLICT)+" data being modified, dataId=" + data_id + ", group=" +
                                 group + ", tenant=" + tenant)
        else:
            self.logger.error(
                "[%s][sub-server-error] dataId=%s, group=%s, tenant=%s, code=%s"
                % (self.get_name(), data_id, group, tenant, str(response))
            )
            raise

    def __request_proxy(self, rpc_client_inner: RpcClient, request: Request, timeout_mills=3000):
        try:
            request.put_all_header(super()._get_security_headers())
            request.put_all_header(super()._get_spas_headers())
            request.put_all_header(super()._get_common_header())
        except NacosException as e:
            raise NacosException(NacosException.CLIENT_INVALID_PARAM + str(e))

        # todo

        return rpc_client_inner.request(request, timeout_mills)

    def __resource_build(self, request: Request) -> str:
        if isinstance(request, ConfigQueryRequest) \
                or isinstance(request, ConfigPublishRequest) \
                or isinstance(request, ConfigRemoveRequest):
            tenant = request.get_tenant()
            group = request.get_group()
            return self.__get_resource(tenant, group)
        return ""

    @staticmethod
    def __get_resource(tenant: str, group: str) -> str:
        if tenant and group:
            return tenant + "+" + group
        if group:
            return group
        if tenant:
            return tenant
        return ""

    def get_one_running_client(self) -> RpcClient:
        return self.__ensure_rpc_client(0)

    def publish_config(self, data_id: str, group: str, tenant: str, app_name: str, tag: str, beta_ips: str,
                       content: str, encrypted_data_key: str, cas_md5: str, config_type: str) -> bool:
        try:
            request = ConfigPublishRequest(dataId=data_id, group=group, tenant=tenant, content=content)
            request.put_addition_param("tag", tag)
            request.put_addition_param("appName", app_name)
            request.put_addition_param("betaIps", beta_ips)
            request.put_addition_param("type", config_type)

            response = self.__request_proxy(self.get_one_running_client(), request)
            if not response.is_success():
                self.logger.warning("[%s] [publish-single] fail, dataId=%s, group=%s, tenant=%s, code=%s, msg=%s"
                                    % (self.get_name(), data_id,
                                       group, tenant, response.get_error_code(), response.get_message()))
                return False
            else:
                content_truncated = content[:100] + "..." if len(content) > 100 else content
                self.logger.info("[%s] [publish-single] ok, dataId=%s, group=%s, tenant=%s, config=%s"
                                 % (self.get_name(), data_id,
                                    group, tenant, content_truncated))
                return True
        except NacosException as e:
            self.logger.warning("[%s][publish-single] error, dataId=%s, group=%s, tenant=%s, code=%s, msg=%s"
                                % (self.__class__.__name__, data_id, group, tenant, "unknown", str(e)))
            return False

    def remove_config(self, data_id: str, group: str, tenant: str, tag: str) -> bool:
        request = ConfigRemoveRequest(dataId=data_id, group=group, tenant=tenant, tag=tag)
        response = self.__request_proxy(self.get_one_running_client(), request)
        return response.is_success()

    def shutdown(self):
        pass

    @staticmethod
    def __get_labels() -> dict:
        labels = {
            RemoteConstants.LABEL_SOURCE: RemoteConstants.LABEL_SOURCE_SDK,
            RemoteConstants.LABEL_MODULE: RemoteConstants.LABEL_MODULE_CONFIG,
            Constants.APPNAME: AppNameUtils.get_app_name(),
            Constants.VIPSERVER_TAG: EnvUtil.get_self_vip_server_tag(),
            Constants.AMORY_TAG: EnvUtil.get_self_amory_tag(),
            Constants.LOCATION_TAG: EnvUtil.get_self_location_tag()
        }
        return labels

    def __init_rpc_client_handler(self, rpc_client_inner: RpcClient) -> None:
        rpc_client_inner.register_server_request_handler(ConfigRpcServerRequestHandler(
            self.cache_map, self.notify_listen_config)
        )

        rpc_client_inner.register_connection_listener(
            ConfigRpcConnectionEventListener()
        )
