from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.config.encryption.encryption_handler import EncryptionHandler
from v2.nacos.config.encryption.encrytion_plugin_manager import EncryptionPluginManager
from v2.nacos.config.encryption.encrytion_plugin_service import EncryptionPluginService
from v2.nacos.config.encryption.kms_aes_128_encrytion_plugin_service import KmsAes128EncryptionPluginService
from v2.nacos.config.encryption.kms_aes_256_encrytion_plugin_service import KmsAes256EncryptionPluginService
from v2.nacos.config.encryption.kms_base_encrytion_plugin_service import KmsBaseEncryptionPluginService
from v2.nacos.config.encryption.kms_client import KmsClient
from v2.nacos.config.filter.config_filter import IConfigFilter
from v2.nacos.config.model.config_param import ConfigParam, HandlerParam, UsageType


def _param_check(param: ConfigParam):
    if param.data_id.startswith(Constants.CIPHER_PRE_FIX) and len(param.content.strip()) != 0:
        return False
    return True


class ConfigEncryptionFilter(IConfigFilter):

    def __init__(self, client_config: ClientConfig):
        encryption_plugin_service = EncryptionPluginService()
        EncryptionPluginManager.join(encryption_plugin_service)
        if client_config.kms_config:
            kms_config = client_config.kms_config
            kms_client = KmsClient.create_kms_client(kms_config)
            kms_aes_128_encryption_plugin_service = KmsAes128EncryptionPluginService(kms_client)
            EncryptionPluginManager.join(kms_aes_128_encryption_plugin_service)
            kms_aes_256_encryption_plugin_service = KmsAes256EncryptionPluginService(kms_client)
            EncryptionPluginManager.join(kms_aes_256_encryption_plugin_service)
            kms_base_encryption_plugin_service = KmsBaseEncryptionPluginService(kms_client)
            EncryptionPluginManager.join(kms_base_encryption_plugin_service)

    def do_filter(self, param: ConfigParam) -> None:
        if _param_check(param):
            return
        if param.usage_type == UsageType.request_type.value:
            encryption_param = HandlerParam(data_id=param.data_id, content=param.content, key_id=param.kms_key_id)
            EncryptionHandler.encrypt_handler(encryption_param)
            param.content = encryption_param.content
            param.encrypted_data_key = encryption_param.encrypted_data_key

        elif param.usage_type == UsageType.response_type.value:
            decryption_param = HandlerParam(data_id=param.data_id, content=param.content,
                                            encrypted_data_key=param.encrypted_data_key)
            EncryptionHandler.decrypt_handler(decryption_param)
            param.content = decryption_param.content
        else:
            raise NacosException(INVALID_PARAM, "param.usage_type must be RequestType or ResponseType")

    def get_order(self) -> int:
        return 0

    def get_filter_name(self) -> str:
        return "defaultConfigEncryptionFilter"
