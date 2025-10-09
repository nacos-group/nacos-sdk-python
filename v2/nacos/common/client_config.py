import logging

from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.common.auth import StaticCredentialsProvider


class KMSConfig:
    def __init__(self, enabled=False, endpoint='', access_key='', secret_key='', client_key_content='', password=''):
        self.enabled = enabled  # 是否启用kms
        self.endpoint = endpoint  # kms服务的地址
        self.client_key_content = client_key_content
        self.password = password
        self.access_key = access_key
        self.secret_key = secret_key


class TLSConfig:
    def __init__(self, enabled=False, appointed=False, ca_file='', cert_file='',
                 key_file='', server_name_override=''):
        self.enabled = enabled  # 是否启用tls
        self.appointed = appointed  # 指明是否使用预设的配置
        self.ca_file = ca_file  # CA证书文件的路径
        self.cert_file = cert_file  # 客户端证书文件的路径
        self.key_file = key_file  # 私钥文件的路径
        self.server_name_override = server_name_override  # 服务器名称覆盖（用于测试）

    def __str__(self):
        return str(self.__dict__)


class GRPCConfig:
    def __init__(self, max_receive_message_length=Constants.GRPC_MAX_RECEIVE_MESSAGE_LENGTH,
                 max_keep_alive_ms=Constants.GRPC_KEEPALIVE_TIME_MILLS,
                 initial_window_size=Constants.GRPC_INITIAL_WINDOW_SIZE,
                 initial_conn_window_size=Constants.GRPC_INITIAL_CONN_WINDOW_SIZE,
                 grpc_timeout=Constants.DEFAULT_GRPC_TIMEOUT_MILLS,
                 capability_negotiation_timeout=Constants.GRPC_CAPABILITY_NEGOTIATION_TIMEOUT):
        self.max_receive_message_length = max_receive_message_length
        self.max_keep_alive_ms = max_keep_alive_ms
        self.initial_window_size = initial_window_size
        self.initial_conn_window_size = initial_conn_window_size
        self.grpc_timeout = grpc_timeout
        self.capability_negotiation_timeout = capability_negotiation_timeout


class ClientConfig:
    def __init__(self, server_addresses=None, endpoint=None, namespace_id='', context_path='', access_key=None,
                 secret_key=None, username=None, password=None, app_name='', app_key='', log_dir='', log_level=None,
                 log_rotation_backup_count=None, app_conn_labels=None, credentials_provider=None):
        self.server_list = []
        try:
            if server_addresses is not None and server_addresses.strip() != "":
                for server_address in server_addresses.strip().split(','):
                    self.server_list.append(server_address.strip())
        except Exception:
            raise NacosException(INVALID_PARAM, "server_addresses is invalid")

        self.endpoint = endpoint
        self.endpoint_context_path = Constants.WEB_CONTEXT
        self.endpoint_query_header = None
        self.namespace_id = namespace_id
        self.credentials_provider = credentials_provider if credentials_provider else StaticCredentialsProvider(access_key, secret_key)
        self.context_path = context_path
        self.username = username  # the username for nacos auth
        self.password = password  # the password for nacos auth
        self.app_name = app_name
        self.app_key = app_key
        self.cache_dir = ''
        self.disable_use_config_cache = False
        self.log_dir = log_dir
        self.log_level = logging.INFO if log_level is None else log_level  # the log level for nacos client, default value is logging.INFO: log_level
        self.log_rotation_backup_count = 7 if log_rotation_backup_count is None else log_rotation_backup_count
        self.timeout_ms = 10 * 1000  # timeout for requesting Nacos server, default value is 10000ms
        self.heart_beat_interval = 5 * 1000  # the time interval for sending beat to server,default value is 5000ms
        self.kms_config = KMSConfig(enabled=False)
        self.tls_config = TLSConfig(enabled=False)
        self.grpc_config = GRPCConfig()
        self.load_cache_at_start = True
        self.update_cache_when_empty = False
        self.app_conn_labels = app_conn_labels
        self.async_update_service = False
        self.update_thread_num = 5

    def set_log_level(self, log_level):
        self.log_level = log_level
        return self

    def set_cache_dir(self, cache_dir):
        self.cache_dir = cache_dir
        return self

    def set_log_dir(self, log_dir):
        self.log_dir = log_dir
        return self

    def set_timeout_ms(self, timeout_ms):
        self.timeout_ms = timeout_ms
        return self

    def set_heart_beat_interval(self, heart_beat_interval):
        self.heart_beat_interval = heart_beat_interval
        return self

    def set_tls_config(self, tls_config: TLSConfig):
        self.tls_config = tls_config
        return self

    def set_kms_config(self, kms_config: KMSConfig):
        self.kms_config = kms_config
        return self

    def set_grpc_config(self, grpc_config: GRPCConfig):
        self.grpc_config = grpc_config
        return self

    def set_load_cache_at_start(self, load_cache_at_start):
        self.load_cache_at_start = load_cache_at_start
        return self

    def set_update_cache_when_empty(self, update_cache_when_empty: bool):
        self.update_cache_when_empty = update_cache_when_empty
        return self

    def set_endpoint_context_path(self, endpoint_context_path):
        self.endpoint_context_path = endpoint_context_path
        return self

    def set_app_conn_labels(self, app_conn_labels: dict):
        self.app_conn_labels = app_conn_labels
        return self

    def set_async_update_service(self, async_update_service: bool):
        self.async_update_service = async_update_service
        return self

    def set_update_thread_num(self, update_thread_num: int):
        self.update_thread_num = update_thread_num
        return self
