import logging
import os

from v2.nacos.config.client_config import ClientConfig


class NacosClient:
    def __init__(self, client_config: ClientConfig):
        self.init_log(client_config)
        self.logger = logging.getLogger(__name__)
        if client_config.timeout_ms <= 0:
            client_config.timeout_ms = 10 * 1000

        if client_config.heart_beat_interval <= 0:
            client_config.heart_beat_interval = 5 * 1000

        self.client_config = client_config

    def init_log(self, client_config: ClientConfig):
        log_level = client_config.log_level or logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        if client_config.cache_dir is None:
            client_config.cache_dir = os.path.join(os.path.expanduser("~"), "nacos", "cache")
        elif not client_config.cache_dir.endswith(os.path.sep):
            client_config.cache_dir += os.path.sep

        if client_config.log_dir is None:
            client_config.log_dir = os.path.join(os.path.expanduser("~"), "nacos", "logs")
        elif not client_config.log_dir.endswith(os.path.sep):
            client_config.log_dir += os.path.sep

        os.makedirs(client_config.log_dir, exist_ok=True)
        self.logger.info(f"log directory: {client_config.log_dir}.")
