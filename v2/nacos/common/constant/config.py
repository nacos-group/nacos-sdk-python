import os
import time
from typing import Dict

class ServerConfig:
    def __init__(self, ip_addr: str, port: int, grpc_port: int = None, scheme: str = 'http', context_path: str = '/nacos'):
        self.scheme = scheme
        self.context_path = context_path
        self.ip_addr = ip_addr
        self.port = port
        self.grpc_port = grpc_port if grpc_port is not None else port + 1000

class ClientConfig:
    def __init__(self):
        self.timeout_ms = 10000  # 毫秒
        self.listen_interval = None  # Deprecated
        self.beat_interval = 5000  # 毫秒
        self.namespace_id = ''
        self.app_name = ''
        self.app_key = ''
        self.endpoint = ''
        self.region_id = ''
        self.access_key = ''
        self.secret_key = ''
        self.open_kms = False
        self.kms_version = KMSVersion()  # 需要定义KMSVersion类
        self.kms_v3_config = KMSv3Config()  # 需要定义KMSv3Config类
        self.cache_dir = os.getcwd()  # 默认为当前路径
        self.disable_use_snapshot = False
        self.update_thread_num = 20
        self.not_load_cache_at_start = False
        self.update_cache_when_empty = False
        self.username = ''
        self.password = ''
        self.log_dir = os.getcwd()  # 默认为当前路径
        self.log_level = 'info'  # 必须是debug, info, warn, error
        self.context_path = ''
        self.append_to_stdout = False
        self.log_sampling = ClientLogSamplingConfig()  # 需要定义ClientLogSamplingConfig类
        self.log_rolling_config = ClientLogRollingConfig()  # 需要定义ClientLogRollingConfig类
        self.tls_cfg = TLSConfig()  # 需要定义TLSConfig类
        self.async_update_service = False
        self.endpoint_context_path = ''
        self.endpoint_query_params = ''
        self.cluster_name = ''
        self.app_conn_labels = {}

class ClientLogSamplingConfig:
    def __init__(self, initial: int, thereafter: int, tick: time.Duration):
        self.initial = initial
        self.thereafter = thereafter
        self.tick = tick

class ClientLogRollingConfig:
    def __init__(self, max_size: int = 100, max_age: int = 0, max_backups: int = 0, local_time: bool = False, compress: bool = False):
        self.max_size = max_size
        self.max_age = max_age
        self.max_backups = max_backups
        self.local_time = local_time
        self.compress = compress

class TLSConfig:
    def __init__(self, appointed: bool = False, enable: bool = False, trust_all: bool = False, ca_file: str = '', cert_file: str = '', key_file: str = '', server_name_override: str = ''):
        self.appointed = appointed
        self.enable = enable
        self.trust_all = trust_all
        self.ca_file = ca_file
        self.cert_file = cert_file
        self.key_file = key_file
        self.server_name_override = server_name_override

class KMSv3Config:
    def __init__(self, client_key_content: str, password: str, endpoint: str, ca_content: str):
        self.client_key_content = client_key_content
        self.password = password
        self.endpoint = endpoint
        self.ca_content = ca_content
