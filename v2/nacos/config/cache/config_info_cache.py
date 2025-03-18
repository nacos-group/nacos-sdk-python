import logging
import os

from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.constants import Constants
from v2.nacos.config.util.config_client_util import get_config_cache_key
from v2.nacos.utils.file_util import read_file, write_to_file

FAILOVER_FILE_SUFFIX = "_failover"
ENCRYPTED_DATA_KEY_FILE_NAME = "encrypted-data-key"


class ConfigInfoCache:
    def __init__(self, client_config: ClientConfig):
        self.logger = logging.getLogger(Constants.CONFIG_MODULE)
        self.config_cache_dir = os.path.join(client_config.cache_dir, Constants.CONFIG_MODULE)
        self.namespace_id = client_config.namespace_id

    async def write_config_to_cache(self, cache_key: str, content: str, encrypted_data_key: str):
        file_path = os.path.join(self.config_cache_dir, cache_key)
        encrypted_data_key_file_path = os.path.join(self.config_cache_dir, ENCRYPTED_DATA_KEY_FILE_NAME,
                                                    cache_key)
        await write_to_file(self.logger, file_path, content)
        await write_to_file(self.logger, encrypted_data_key_file_path, encrypted_data_key)

    async def get_config_cache(self, data_id: str, group: str):
        cache_key = get_config_cache_key(data_id, group, self.namespace_id)
        file_path = os.path.join(self.config_cache_dir, cache_key)
        config_content = await read_file(self.logger, file_path)
        if not data_id.startswith(Constants.CIPHER_PRE_FIX):
            return config_content, ""
        else:
            encrypted_data_key_file_path = os.path.join(self.config_cache_dir, ENCRYPTED_DATA_KEY_FILE_NAME,
                                                        cache_key)
            config_encrypted_data_key = await read_file(self.logger, encrypted_data_key_file_path)
            return config_content, config_encrypted_data_key

    async def get_fail_over_config_cache(self, data_id: str, group: str):
        cache_key = get_config_cache_key(data_id, group, self.namespace_id) + FAILOVER_FILE_SUFFIX
        file_path = os.path.join(self.config_cache_dir, cache_key)
        config_content = await read_file(self.logger, file_path)
        if not config_content:
            return "", ""
        self.logger.info(f"get fail over content, namespace:{self.namespace_id}, group:{group}, dataId:{data_id}")
        encrypted_data_key_path = os.path.join(self.config_cache_dir, ENCRYPTED_DATA_KEY_FILE_NAME,
                                               cache_key)
        config_encrypted_data_key = await read_file(self.logger, encrypted_data_key_path)
        return config_content, config_encrypted_data_key
