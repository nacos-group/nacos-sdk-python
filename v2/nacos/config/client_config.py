import logging
import os


class KMSConfig:
    def __init__(self, enabled=False, appointed=False, ak='', sk='',
                 region_id='', endpoint=''):
        self.enabled = enabled  # 是否启用kms
        self.appointed = appointed  # 指明是否使用预设的配置
        self.ak = ak  # 阿里云账号的AccessKey
        self.sk = sk  # 阿里云账号的SecretKey
        self.region_id = region_id  # 阿里云账号的区域
        self.endpoint = endpoint  # kms服务的地址


class TLSConfig:
    def __init__(self, enabled=False, appointed=False, ca_file='', cert_file='',
                 key_file='', server_name_override=''):
        self.enabled = enabled  # 是否启用tls
        self.appointed = appointed  # 指明是否使用预设的配置
        self.ca_file = ca_file  # CA证书文件的路径
        self.cert_file = cert_file  # 客户端证书文件的路径
        self.key_file = key_file  # 私钥文件的路径
        self.server_name_override = server_name_override  # 服务器名称覆盖（用于测试）


class ClientConfig:
    def __init__(self, server_address=None, endpoint=None, namespace_id='', access_key=None,
                 secret_key=None, username=None, password=None):
        self.server_address = server_address
        self.endpoint = endpoint
        self.namespace_id = namespace_id
        self.access_key = access_key
        self.secret_key = secret_key
        self.username = username  # the username for nacos auth
        self.password = password  # the password for nacos auth

        self.cache_dir = ''
        self.log_dir = ''
        self.log_level = logging.INFO
        self.timeout_ms = 10 * 1000  # timeout for requesting Nacos server, default value is 10000ms
        self.heart_beat_interval = 5 * 1000  # the time interval for sending beat to server,default value is 5000ms
        self.kms_config = None
        self.tls_config = None
        self.not_load_cache_at_start = False

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

    def set_not_load_cache_at_start(self, not_load_cache_at_start):
        self.not_load_cache_at_start = not_load_cache_at_start
        return self
