import queue
import time
import uuid
from concurrent.futures.thread import ThreadPoolExecutor
from threading import RLock

from v2.nacos.ability.client_abilities import ClientAbilities
from v2.nacos.common.constants import Constants
from v2.nacos.common.lifecycle.closeable import Closeable
from v2.nacos.common.utils import get_current_time_millis
from v2.nacos.config.abstract.abstract_config_transport_client import AbstractConfigTransportClient
from v2.nacos.config.common.group_key import GroupKey
from v2.nacos.config.filter_impl.config_response import ConfigResponse
from v2.nacos.config.ilistener import Listener
from v2.nacos.config.impl.cache_data import CacheData
from v2.nacos.config.impl.config_change_notify_request_handler import ConfigChangeNotifyRequestHandler
from v2.nacos.config.impl.config_rpc_connection_event_listener import ConfigRpcConnectionEventListener
from v2.nacos.config.impl.config_rpc_server_list_factory import ConfigRpcServerListFactory
# from v2.nacos.config.impl.config_rpc_transport_client import ConfigRpcTransportClient
from v2.nacos.config.impl.local_config_info_processor import LocalConfigInfoProcessor
from v2.nacos.config.impl.local_encrypted_data_key_processor import LocalEncryptedDataKeyProcessor
from v2.nacos.config.impl.server_list_manager import ServerListManager
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.property_key_constants import PropertyKeyConstants
from v2.nacos.remote.remote_constants import RemoteConstants
from v2.nacos.remote.requests.config_batch_listen_request import ConfigBatchListenRequest
from v2.nacos.remote.requests.config_query_request import ConfigQueryRequest
from v2.nacos.remote.requests.config_publish_request import ConfigPublishRequest
from v2.nacos.remote.requests.config_remove_request import ConfigRemoveRequest
from v2.nacos.remote.requests.request import Request
from v2.nacos.remote.responses import ConfigQueryResponse
from v2.nacos.remote.rpc_client import RpcClient
from v2.nacos.remote.rpc_client_factory import RpcClientFactory
from v2.nacos.remote.utils import ConnectionType
from v2.nacos.utils.app_name_utils import AppNameUtils


class ClientWorker(Closeable):
    MAX_WORKER = 4

    def __init__(self, logger, config_filter_chain_manager, server_list_manager, properties):
        self.logger = logger
        self.cache_map = {}
        self.config_filter_chain_manager = config_filter_chain_manager
        self.health_server = True
        self.uuid = uuid.uuid4()
        self.timeout = None
        self.agent = ClientWorker.ConfigRpcTransportClient(
            logger, properties, server_list_manager, self
        )
        self.task_penalty_time = None
        self.enable_remote_sync_config = False
        self.lock = RLock()

        self.__init_properties(properties)

        executor_service = ThreadPoolExecutor(max_workers=ClientWorker.MAX_WORKER)

        self.agent.set_executor(executor_service)
        self.agent.start()

    def __init_properties(self, properties: dict) -> None:
        # todo
        self.enable_remote_sync_config = properties.get(PropertyKeyConstants.ENABLE_REMOTE_SYNC_CONFIG)
        if not self.enable_remote_sync_config:
            self.enable_remote_sync_config = False

    @staticmethod
    def __blank_2_default_group(group: str) -> str:
        if not group or not group.strip():
            return Constants.DEFAULT_GROUP
        else:
            return group.strip()

    def add_listeners(self, data_id: str, group: str, listeners: list) -> None:
        group = self.__blank_2_default_group(group)
        tenant = self.agent.get_tenant()
        cache = self.add_cache_data_if_absent(data_id, group, tenant)
        with self.lock:
            for listener in listeners:
                cache.add_listener(listener)
            cache.set_sync_with_server(False)
            self.agent.notify_listen_config()

    def add_tenant_listeners(self, data_id: str, group: str, listeners: list) -> None:
        group = self.__blank_2_default_group(group)
        tenant = self.agent.get_tenant()
        cache = self.add_cache_data_if_absent(data_id, group, tenant)

        # debug
        # print("at add_tenant_listener, cache_map:", str(self.cache_map))

        with self.lock:
            for listener in listeners:
                cache.add_listener(listener)
            cache.set_sync_with_server(False)
            self.agent.notify_listen_config()

    def add_tenant_listeners_with_content(self, data_id: str, group: str, content: str, listeners: list) -> None:
        group = self.__blank_2_default_group(group)
        tenant = self.agent.get_tenant()
        cache = self.add_cache_data_if_absent(data_id, group, tenant)
        with self.lock:
            cache.set_content(content)
            for listener in listeners:
                cache.add_listener(listener)
            cache.set_sync_with_server(False)
            self.agent.notify_listen_config()

    def remove_listener(self, data_id: str, group: str, listener: Listener) -> None:
        group = self.__blank_2_default_group(group)
        cache = self.get_cache(data_id, group, "")
        if cache:
            with self.lock:
                cache.remove_listener(listener)
                if not cache.get_listeners():
                    cache.set_sync_with_server(False)
                    self.agent.remove_cache(data_id, group)

    def remove_tenant_listener(self, data_id: str, group: str, listener: Listener) -> None:
        group = self.__blank_2_default_group(group)
        tenant = self.agent.get_tenant()
        cache = self.get_cache(data_id, group, tenant)
        if cache:
            with self.lock:
                cache.remove_listener(listener)
                if not cache.get_listeners():
                    cache.set_sync_with_server(False)
                    self.agent.remove_cache(data_id, group)

    def remove_cache(self, data_id: str, group: str, tenant: str) -> None:
        group_key = GroupKey.get_key_tenant(data_id, group, tenant)
        with self.lock:
            # debug
            # print("remove", group_key, "from:", self.cache_map)
            copy = self.cache_map.copy()
            copy.pop(group_key)
            self.cache_map = copy
        self.logger.info("[%s] [unsubscribe] %s" % (self.agent.get_name(), group_key))

    def remove_config(self, data_id: str, group: str, tenant: str, tag: str):
        return self.agent.remove_config(data_id, group, tenant, tag)

    def publish_config(self, data_id: str, group: str, tenant: str, app_name: str, tag: str, beta_ips: str,
                       content: str, encrypted_data_key: str, cas_md5: str, config_type: str) -> bool:
        return self.agent.publish_config(
            data_id, group, tenant, app_name, tag, beta_ips, content, encrypted_data_key, cas_md5, config_type
        )

    def add_cache_data_if_absent(self, data_id: str, group: str, tenant: str) -> CacheData:
        cache = self.get_cache(data_id, group, tenant)
        if cache:
            return cache

        key = GroupKey.get_key(data_id, group, tenant)

        with self.lock:
            cache_from_map = self.get_cache(data_id, group, tenant)
            if cache_from_map:
                cache = cache_from_map
                cache.set_sync_with_server(True)
            else:
                cache = CacheData(
                    self.logger, self.config_filter_chain_manager, self.agent.get_name(), data_id, group, tenant
                )
                task_id = len(self.cache_map) / CacheData.PER_TASK_CONFIG_SIZE
                cache.set_task_id(int(task_id))
                if self.enable_remote_sync_config:
                    response = self.get_server_config(data_id, group, tenant, 3000, False)
                    cache.set_content(response.get_content())

            copy = self.cache_map.copy()
            copy[key] = cache
            self.cache_map = copy

            # debug
            # print("add cache:", str(self.cache_map))

        self.logger.info("[%s] [subscribe] %s" % (self.agent.get_name(), key))

        return cache

    def get_cache(self, data_id: str, group: str, tenant: str) -> CacheData:
        if not data_id or not group:
            raise NacosException()
        return self.cache_map.get(GroupKey.get_key_tenant(data_id, group, tenant))

    def get_server_config(
            self, data_id: str, group: str, tenant: str, read_timeout: int, notify: bool) -> ConfigResponse:
        if not group:
            group = Constants.DEFAULT_GROUP
        return self.agent.query_config(data_id, group, tenant, read_timeout, notify)

    def is_health_server(self) -> bool:
        return self.health_server

    def set_health_server(self, health_server: bool) -> None:
        self.health_server = health_server

    def get_agent_name(self) -> str:
        return self.agent.get_name()

    def shutdown(self) -> None:
        self.logger.info("%s do shutdown begin" % self.__class__.__name__)
        if self.agent:
            self.agent.shutdown()
        self.logger.info("%s do shutdown stop" % self.__class__.__name__)

    class ConfigRpcTransportClient(AbstractConfigTransportClient):
        ALL_SYNC_INTERNAL = 5 * 60 * 1000

        RPC_AGENT_NAME = "config_rpc_client"

        def __init__(
                self, logger, properties: dict, server_list_manager: ServerListManager, client_worker
        ):
            super().__init__(logger, properties, server_list_manager)
            self.listen_execute_bell = queue.Queue()
            self.bell_item = object()
            self.last_all_sync_time = get_current_time_millis()
            self.uuid = uuid.uuid4()
            self.lock = RLock()
            self.local_config_info_processor = LocalConfigInfoProcessor(logger)
            self.local_encrypted_data_key_processor = LocalEncryptedDataKeyProcessor(logger)

            self.client_worker = client_worker

        def start_internal(self) -> None:
            self.executor.submit(self.__start_run)

        def __start_run(self) -> None:
            while self.executor:
                try:
                    try:
                        self.listen_execute_bell.get(timeout=5)
                    except Exception:
                        pass
                    self.execute_config_listen()
                except NacosException as e:
                    self.logger.error("[rpc listen execute] [rpc listen] exception " + str(e))

        def get_name(self) -> str:
            return ClientWorker.ConfigRpcTransportClient.RPC_AGENT_NAME

        def notify_listen_config(self) -> None:
            self.listen_execute_bell.put(self.bell_item)

        def execute_config_listen(self) -> None:
            listen_caches_map = {}
            remove_listen_caches_map = {}
            now = get_current_time_millis()
            need_all_sync = (now - self.last_all_sync_time) >= ClientWorker.ConfigRpcTransportClient.ALL_SYNC_INTERNAL

            # categorize cache_data

            # debug
            # print("at execute_config_listen, cache_map:", self.client_worker.cache_map)

            for cache in self.client_worker.cache_map.values():
                with self.lock:
                    if cache.is_sync_with_server():
                        cache.check_listener_md5()
                        if not need_all_sync:
                            continue

                    if cache.get_listeners():
                        if not cache.is_use_local_config_info():
                            cache_data_list = listen_caches_map.get(str(cache.get_task_id()))
                            if not cache_data_list:
                                cache_data_list = []
                                listen_caches_map[str(cache.get_task_id())] = cache_data_list
                            cache_data_list.append(cache)
                    elif not cache.get_listeners():
                        if not cache.is_use_local_config_info():
                            cache_data_list = remove_listen_caches_map.get(str(cache.get_task_id()))
                            if not cache_data_list:
                                cache_data_list = []
                                remove_listen_caches_map[str(cache.get_task_id())] = cache_data_list
                            cache_data_list.append(cache)

            has_changed_keys = False

            if listen_caches_map:
                for task_id, listen_caches in listen_caches_map.items():
                    time_stamp_map = {}
                    for cache_data in listen_caches:
                        time_stamp_map[
                            GroupKey.get_key_tenant(cache_data.data_id, cache_data.group, cache_data.tenant)
                        ] = cache_data.get_last_modified_ts()

                    config_change_listen_request = self.__build_config_request(listen_caches)
                    config_change_listen_request.listen = True
                    try:
                        rpc_client = self.__ensure_rpc_client(task_id)
                        config_change_batch_listen_response = self.__request_proxy(rpc_client,
                                                                                   config_change_listen_request)
                        if config_change_batch_listen_response and config_change_batch_listen_response.is_success():
                            change_keys = []
                            if config_change_batch_listen_response.get_changed_configs():
                                has_changed_keys = True
                                for change_config in config_change_batch_listen_response.get_changed_configs():
                                    change_key = GroupKey.get_key_tenant(
                                        change_config.dataId, change_config.group, change_config.tenant
                                    )
                                    change_keys.append(change_key)
                                    initializing = self.client_worker.cache_map.get(change_key).is_initializing()
                                    self.__refresh_content_and_check(change_key, not initializing)

                            for cache_data in listen_caches:
                                group_key = GroupKey.get_key_tenant(cache_data.data_id, cache_data.group,
                                                                    cache_data.tenant)
                                if group_key not in change_keys:
                                    with self.lock:
                                        if cache_data.get_listeners():
                                            previous_time_stamp = time_stamp_map.get(group_key)
                                            if previous_time_stamp:
                                                cache_data.set_last_modified_ts(get_current_time_millis())
                                            cache_data.set_sync_with_server(True)
                                cache_data.set_initializing(False)
                    except NacosException as e:
                        self.logger.error("Async listen config change error " + str(e))
                    time.sleep(0.05)

            if remove_listen_caches_map:
                for task_id, remove_listen_caches in remove_listen_caches_map.items():
                    config_change_listen_request = self.__build_config_request(remove_listen_caches)
                    config_change_listen_request.listen = False
                    try:
                        rpc_client = self.__ensure_rpc_client(task_id)
                        remove_success = self.__un_listen_config_change(rpc_client, config_change_listen_request)
                        if remove_success:
                            for cache_data in remove_listen_caches:
                                with self.lock:
                                    if not cache_data.get_listeners():
                                        self.client_worker.remove_cache(
                                            cache_data.data_id, cache_data.group, cache_data.tenant
                                        )
                    except NacosException as e:
                        self.logger.error("async remove listen config change error " + str(e))
                    time.sleep(0.05)

            if need_all_sync:
                self.last_all_sync_time = now

            if has_changed_keys:
                self.notify_listen_config()

        def __refresh_content_and_check(self, group_key: str, notify: bool) -> None:
            if self.client_worker.cache_map and group_key in self.client_worker.cache_map.keys():
                cache_data = self.client_worker.cache_map.get(group_key)
                try:
                    response = self.get_server_config(cache_data.data_id, cache_data.group, cache_data.tenant, 3000,
                                                      notify)
                    cache_data.set_content(response.get_content())
                    cache_data.set_encrypted_data_key(response.get_encrypted_data_key())
                    if response.get_config_type():
                        cache_data.set_type(response.get_config_type())
                    if notify:
                        content_truncated = response.get_content()[:100] + "..." if len(response.get_content()) > 100 \
                            else response.get_content()
                        self.logger.info(
                            "[%s] [data-received] dataId=%s, group=%s, tenant=%s, md5=%s, content=%s, type=%s"
                            % (self.get_name(), cache_data.data_id,
                               cache_data.group, cache_data.tenant, cache_data.md5, content_truncated,
                               response.get_config_type())
                            )
                    cache_data.check_listener_md5()
                except NacosException as e:
                    self.logger.error("refresh content and check md5 fail, dataId=%s, group=%s, tenant=%s: %s"
                                      % (cache_data.data_id, cache_data.group, cache_data.tenant, str(e))
                                      )

        def get_server_config(self, data_id: str, group: str, tenant: str, read_timeout: int, notify: bool) \
                -> ConfigResponse:
            if not group:
                group = Constants.DEFAULT_GROUP
            return self.query_config(data_id, group, tenant, read_timeout, notify)

        def __ensure_rpc_client(self, task_id: str) -> RpcClient:
            with self.lock:
                labels = self.__get_labels()
                new_labels = labels.copy()
                new_labels["taskId"] = task_id

                client_name = str(self.uuid) + "_config-" + task_id
                rpc_client = RpcClientFactory(self.logger).create_client(client_name, ConnectionType.GRPC, new_labels)

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
            # todo
            self.notify_listen_config()

        def __un_listen_config_change(self, rpc_client: RpcClient,
                                      config_change_listen_request: ConfigBatchListenRequest) -> bool:
            response = self.__request_proxy(rpc_client, config_change_listen_request)
            return response.is_success()

        def query_config(self, data_id: str, group: str, tenant: str, read_timeout: int,
                         notify: bool) -> ConfigResponse:
            request = ConfigQueryRequest.build(data_id, group, tenant)
            request.put_header("notify", str(notify))
            rpc_client = self.get_one_running_client()

            if notify:
                cache_data = self.client_worker.cache_map.get(GroupKey.get_key_tenant(data_id, group, tenant))
                if cache_data:
                    rpc_client = self.__ensure_rpc_client(str(cache_data.get_task_id()))

            response = self.__request_proxy(rpc_client, request, read_timeout)
            config_response = ConfigResponse()
            if response.is_success():
                self.local_config_info_processor.save_snapshot(
                    self.get_name(), data_id, group, tenant, response.get_content())
                config_response.set_content(response.get_content())
                if response.get_content_type():
                    config_type = response.get_content_type()
                else:
                    config_type = "text"

                config_response.set_config_type(config_type)
                encrypted_data_key = response.get_encrypted_data_key()
                self.local_encrypted_data_key_processor.save_encrypt_data_key_snapshot(
                    self.get_name(), data_id, group, tenant, encrypted_data_key
                )
                return config_response
            elif response.get_error_code() == ConfigQueryResponse.CONFIG_NOT_FOUND:
                self.local_config_info_processor.save_snapshot(self.get_name(), data_id, group, tenant, None)
                self.local_encrypted_data_key_processor.save_snapshot(self.get_name(), data_id, group, tenant, None)
                return config_response
            elif response.get_error_code() == ConfigQueryResponse.CONFIG_QUERY_CONFLICT:
                self.logger.error(
                    "[%s][sub-server-error] get server config "
                    "being modified concurrently, dataId=%s, group=%s, tanant=%s"
                    % (self.get_name(), data_id, group, tenant)
                )
                raise NacosException(
                    str(NacosException.CONFLICT) + " data being modified, dataId=" + data_id + ", group=" +
                    group + ", tenant=" + tenant)
            else:
                self.logger.error(
                    "[%s][sub-server-error] dataId=%s, group=%s, tenant=%s, code=%s"
                    % (self.get_name(), data_id, group, tenant, str(response))
                )
                raise NacosException(
                    str(response.get_error_code()) + " http error, code=" + str(
                        response.get_error_code()) + ", dataId=" +
                    data_id + ", group=" + group + ", tenant=" + tenant
                )

        def __request_proxy(self, rpc_client_inner: RpcClient, request: Request, timeout_mills=3000):
            try:
                request.put_all_header(super()._get_security_headers())
                request.put_all_header(super()._get_spas_headers())
                request.put_all_header(super()._get_common_header())
            except NacosException as e:
                raise NacosException(NacosException.CLIENT_INVALID_PARAM + str(e))

            # todo limiter

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
            return self.__ensure_rpc_client("0")

        def publish_config(self, data_id: str, group: str, tenant: str, app_name: str, tag: str, beta_ips: str,
                           content: str, encrypted_data_key: str, cas_md5: str, config_type: str) -> bool:
            try:
                request = ConfigPublishRequest(dataId=data_id, group=group, tenant=tenant, content=content)
                request.put_addition_param("tag", tag)
                request.put_addition_param("appName", app_name)
                request.put_addition_param("betaIps", beta_ips)
                request.put_addition_param("type", config_type)
                request.put_addition_param("encryptedDataKey", encrypted_data_key)
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
            with self.lock:
                self.logger.info("Trying to shutdown transport client")
                all_client_entries = RpcClientFactory(self.logger).get_all_client_entries()
                for key in list(all_client_entries.items()):
                    key.startswith(str(self.uuid))
                    self.logger.info("Trying to shutdown rpc client " + key)
                    try:
                        all_client_entries[key].shutdown()
                    except NacosException as e:
                        print(e)
                    self.logger.info("Remove rpc client " + key)
                    del all_client_entries[key]

                self.logger.info("Shutdown executor " + str(self.executor))
                self.executor.shutdown(wait=False)

                for value in self.client_worker.cache_map.values():
                    value.set_sync_with_server(False)

        @staticmethod
        def __get_labels() -> dict:
            # todo
            return {}

        def __init_rpc_client_handler(self, rpc_client_inner: RpcClient) -> None:
            rpc_client_inner.register_server_request_handler(ConfigChangeNotifyRequestHandler(
                self.logger, self.client_worker.cache_map, self.notify_listen_config)
            )

            rpc_client_inner.register_connection_listener(
                ConfigRpcConnectionEventListener(self.logger, rpc_client_inner, self.client_worker.cache_map,
                                                 self.notify_listen_config)
            )

            rpc_client_inner.set_server_list_factory(
                ConfigRpcServerListFactory(self.server_list_manager)
            )

