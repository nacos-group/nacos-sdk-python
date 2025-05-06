from typing import Dict

from v2.nacos.common.client_config import KMSConfig
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.config.encryption.kms_client import KmsClient
from v2.nacos.config.encryption.plugin.encryption_plugin import EncryptionPlugin
from v2.nacos.config.encryption.plugin.kms_aes_128_encrytion_plugin import KmsAes128EncryptionPlugin
from v2.nacos.config.encryption.plugin.kms_aes_256_encrytion_plugin import KmsAes256EncryptionPlugin
from v2.nacos.config.encryption.plugin.kms_base_encryption_plugin import KmsBaseEncryptionPlugin
from v2.nacos.config.model.config_param import HandlerParam


class KMSHandler:
    def __init__(self, kms_config: KMSConfig):
        self.kms_plugins: Dict[str, EncryptionPlugin] = {}
        self.kms_client = KmsClient.create_kms_client(kms_config)
        kms_aes_128_encryption_plugin = KmsAes128EncryptionPlugin(self.kms_client)
        self.kms_plugins[kms_aes_128_encryption_plugin.algorithm_name()] = kms_aes_128_encryption_plugin
        kms_aes_256_encryption_plugin = KmsAes256EncryptionPlugin(self.kms_client)
        self.kms_plugins[kms_aes_256_encryption_plugin.algorithm_name()] = kms_aes_256_encryption_plugin
        kms_base_encryption_plugin = KmsBaseEncryptionPlugin(self.kms_client)
        self.kms_plugins[kms_base_encryption_plugin.algorithm_name()] = kms_base_encryption_plugin

    def find_encryption_service(self, data_id: str):
        for algorithm_name in self.kms_plugins:
            if data_id.startswith(algorithm_name):
                return self.kms_plugins[algorithm_name]
        raise NacosException(INVALID_PARAM, f"encryption plugin service not found, data_id:{data_id}")

    @staticmethod
    def check_param(handler_param: HandlerParam):
        if not handler_param.data_id.startswith(Constants.CIPHER_PRE_FIX):
            raise NacosException(INVALID_PARAM, "dataId prefix should start with 'cipher-'")
        if len(handler_param.content) == 0:
            raise NacosException(INVALID_PARAM, "encrypt empty content error")

    def encrypt_handler(self, handler_param: HandlerParam):
        self.check_param(handler_param)
        plugin = self.find_encryption_service(handler_param.data_id)
        handler_param = plugin.generate_secret_key(handler_param)
        return plugin.encrypt(handler_param)

    def decrypt_handler(self, handler_param: HandlerParam):
        self.check_param(handler_param)
        plugin = self.find_encryption_service(handler_param.data_id)
        handler_param.plain_data_key = plugin.decrypt_secret_key(handler_param)
        return plugin.decrypt(handler_param)
