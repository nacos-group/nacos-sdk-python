import logging
import os
from logging.handlers import TimedRotatingFileHandler

from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.transport.http_agent import HttpAgent


class NacosClient:
    def __init__(self, client_config: ClientConfig, log_file: str):
        if not client_config:
            raise NacosException(INVALID_PARAM, "client config is required")

        self.logger = None
        self.init_log(client_config, log_file)

        if client_config.timeout_ms <= 0:
            client_config.timeout_ms = 10 * 1000

        if client_config.heart_beat_interval <= 0:
            client_config.heart_beat_interval = 5 * 1000

        self.client_config = client_config
        self.http_agent = HttpAgent(self.logger, client_config.tls_config, client_config.timeout_ms)

    def init_log(self, client_config: ClientConfig, module):
        log_level = client_config.log_level or logging.INFO

        if client_config.cache_dir == '':
            client_config.cache_dir = os.path.join(os.path.expanduser("~"), "nacos", "cache")

        if not client_config.cache_dir.endswith(os.path.sep):
            client_config.cache_dir += os.path.sep

        if client_config.log_dir is None or client_config.log_dir.strip() == '':
            client_config.log_dir = os.path.join(os.path.expanduser("~"), "logs", "nacos")

        if not client_config.log_dir.endswith(os.path.sep):
            client_config.log_dir += os.path.sep

        os.makedirs(client_config.log_dir, exist_ok=True)
        os.makedirs(client_config.cache_dir, exist_ok=True)

        log_path = client_config.log_dir + module + ".log"
        self.logger = logging.getLogger(module)

        file_handler = TimedRotatingFileHandler(log_path, when="midnight", interval=1,
                                                backupCount=client_config.log_rotation_backup_count,
                                                encoding='utf-8')
        self.logger.setLevel(log_level)

        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.propagate = False
        self.logger.info(f"log directory: {client_config.log_dir}.")
