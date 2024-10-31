import logging
import os

from v2.nacos.common import disk_cache
from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.constants import Constants
from v2.nacos.config.model.config_param import ConfigParam
from v2.nacos.utils import common_util


class ConfigCache:
    def __init__(self, client_config: ClientConfig):
        self.logger = logging.getLogger(Constants.CONFIG_MODULE)
        self.config_cache_dir = os.path.join(client_config.cache_dir, Constants.CONFIG_MODULE)
        self.namespace_id = client_config.namespace_id

    def load_cache_from_disk(self, cache_key: str, is_cipher: bool):
        try:
            cache_content = disk_cache.read_config_from_file(cache_key, self.config_cache_dir)
            if not is_cipher:
                return cache_content, ""
            encrypted_data_key = disk_cache.read_encrypted_data_key_from_file(cache_key, self.config_cache_dir)
            return cache_content, encrypted_data_key
        except Exception as e:
            self.logger.error(f"[load_cache_from_disk] fail to load cache from disk, error:{str(e)}")
            raise

    def write_cache_to_disk(self, cache_key: str, content: str, encrypted_data_key: str):
        try:
            disk_cache.write_config_to_file(cache_key, self.config_cache_dir, content)
            disk_cache.write_encrypted_data_key_to_file(cache_key, self.config_cache_dir,
                                                        encrypted_data_key)
        except Exception as e:
            self.logger.error(f"[write_cache_to_disk] fail to write cache to disk, error:{str(e)}")
            raise

    def load_failover_cache_from_disk(self, cache_key: str):
        content = disk_cache.get_failover(cache_key, self.config_cache_dir)
        if content:
            encrypted_data_key = disk_cache.get_failover_encrypted_data_key(cache_key, self.config_cache_dir)
            return content, encrypted_data_key
        else:
            self.logger.info("[load_failover_cache_from_disk] no cache file found, skip loading cache from disk.")
            return "", ""

    def get_config_cache_key(self, param: ConfigParam):
        cache_key = common_util.get_config_cache_key(param.data_id, param.group, self.namespace_id)
        return cache_key
