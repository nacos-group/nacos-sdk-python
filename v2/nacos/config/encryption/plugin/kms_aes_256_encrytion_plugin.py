from v2.nacos.common.constants import Constants
from v2.nacos.config.encryption.plugin.kms_encrytion_plugin import KmsEncryptionPlugin
from v2.nacos.config.encryption.kms_client import KmsClient
from v2.nacos.config.model.config_param import HandlerParam


class KmsAes256EncryptionPlugin(KmsEncryptionPlugin):
    def __init__(self, kms_client: KmsClient):
        super().__init__(kms_client)
        self.ALGORITHM = 'cipher-kms-aes-256'

    def generate_secret_key(self, handler_param: HandlerParam) -> HandlerParam:
        key_id = handler_param.key_id if handler_param.key_id.strip() else Constants.MSE_KMS_V1_DEFAULT_KEY_ID

        plain_secret_key, encryted_secret_key = self.kms_client.generate_secret_key(key_id, 'AES_256')
        handler_param.plain_data_key = plain_secret_key
        handler_param.encrypted_data_key = encryted_secret_key
        return handler_param

    def algorithm_name(self):
        return self.ALGORITHM
