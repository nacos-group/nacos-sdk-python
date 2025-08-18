from typing import Dict, List

from v2.nacos.common.auth import CredentialsProvider, StaticCredentialsProvider
from v2.nacos.common.client_config import ClientConfig, GRPCConfig
from v2.nacos.common.client_config import KMSConfig
from v2.nacos.common.client_config import TLSConfig
from v2.nacos.common.constants import Constants


class ClientConfigBuilder:
    def __init__(self):
        self._config = ClientConfig()

    def server_address(self, server_address: str) -> "ClientConfigBuilder":
        if server_address is not None and server_address.strip() != "":
            for server_address in server_address.strip().split(','):
                self._config.server_list.append(server_address.strip())
        return self

    def endpoint(self, endpoint) -> "ClientConfigBuilder":
        self._config.endpoint = endpoint
        return self

    def namespace_id(self, namespace_id: str) -> "ClientConfigBuilder":
        if namespace_id is None:
            namespace_id = Constants.DEFAULT_NAMESPACE_ID
        self._config.namespace_id = namespace_id
        return self

    def timeout_ms(self, timeout_ms) -> "ClientConfigBuilder":
        self._config.timeout_ms = timeout_ms
        return self

    def heart_beat_interval(self, heart_beat_interval) -> "ClientConfigBuilder":
        self._config.heart_beat_interval = heart_beat_interval
        return self

    def log_level(self, log_level) -> "ClientConfigBuilder":
        self._config.log_level = log_level
        return self

    def log_dir(self, log_dir: str) -> "ClientConfigBuilder":
        self._config.log_dir = log_dir
        return self

    def access_key(self, access_key: str) -> "ClientConfigBuilder":
        if not self._config.credentials_provider:
            self._config.credentials_provider = StaticCredentialsProvider(access_key_id=access_key)
        else:
            self._config.credentials_provider.set_access_key_id(access_key)
        return self

    def secret_key(self, secret_key: str) -> "ClientConfigBuilder":
        if not self._config.credentials_provider:
            self._config.credentials_provider = StaticCredentialsProvider(access_key_secret=secret_key)
        else:
            self._config.credentials_provider.set_access_key_secret(secret_key)
        return self

    def credentials_provider(self, credentials_provider: CredentialsProvider) -> "ClientConfigBuilder":
        self._config.credentials_provider = credentials_provider
        return self

    def username(self, username: str) -> "ClientConfigBuilder":
        self._config.username = username
        return self

    def password(self, password: str) -> "ClientConfigBuilder":
        self._config.password = password
        return self

    def cache_dir(self, cache_dir: str) -> "ClientConfigBuilder":
        self._config.cache_dir = cache_dir
        return self

    def tls_config(self, tls_config: TLSConfig) -> "ClientConfigBuilder":
        self._config.tls_config = tls_config
        return self

    def kms_config(self, kms_config: KMSConfig) -> "ClientConfigBuilder":
        self._config.kms_config = kms_config
        return self

    def grpc_config(self, grpc_config: GRPCConfig) -> "ClientConfigBuilder":
        self._config.grpc_config = grpc_config
        return self

    def load_cache_at_start(self, load_cache_at_start: bool) -> "ClientConfigBuilder":
        self._config.load_cache_at_start = load_cache_at_start
        return self

    def app_conn_labels(self, app_conn_labels: dict) -> "ClientConfigBuilder":
        if self._config.app_conn_labels is None:
            self._config.app_conn_labels = {}
        self._config.app_conn_labels.update(app_conn_labels)
        return self

    def endpoint_query_header(self, endpoint_query_header: Dict[str, str]) -> "ClientConfigBuilder":
        if self._config.endpoint_query_header is None:
            self._config.endpoint_query_header = {}
        self._config.endpoint_query_header.update(endpoint_query_header)
        return self

    def async_update_service(self, async_update_service: bool) -> "ClientConfigBuilder":
        self._config.set_async_update_service(async_update_service)
        return self

    def update_thread_num(self, update_thread_num: int) -> "ClientConfigBuilder":
        self._config.update_thread_num = update_thread_num
        return self

    def build(self):
        return self._config
