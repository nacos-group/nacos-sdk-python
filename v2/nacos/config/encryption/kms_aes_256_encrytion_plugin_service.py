from v2.nacos.common.constants import Constants
from v2.nacos.config.encryption.kms_aes_encrytion_plugin_service import KmsAesEncryptionPluginService
from v2.nacos.config.encryption.kms_client import KmsClient
from v2.nacos.config.model.config_param import HandlerParam


class KmsAes256EncryptionPluginService(KmsAesEncryptionPluginService):
    def __init__(self, kms_client: KmsClient):
        super().__init__(kms_client)
        self.ALGORITHM = 'cipher-kms-aes-256'

    def key_id_param_check(self, key_id: str):
        return super().key_id_param_check(key_id)

    def encrypt(self, handler_param: HandlerParam):
        super().encrypt(handler_param)

    def decrypt(self, handler_param: HandlerParam):
        super().decrypt(handler_param)

    def generate_secret_key(self, handler_param: HandlerParam):
        key_id = self.key_id_param_check(handler_param.key_id)
        plain_secret_key, encryted_secret_key = self.kms_client.generate_secret_key(key_id,
                                                                                    Constants.KMS_AES_256_ALGORITHM_NAME)
        handler_param.plain_data_key = plain_secret_key
        handler_param.encrypted_data_key = encryted_secret_key

    def algorithm_name(self):
        return self.ALGORITHM

    def encrypt_secret_key(self, handler_param: HandlerParam):
        super().encrypt_secret_key(handler_param)

    def decrypt_secret_key(self, handler_param: HandlerParam):
        super().decrypt_secret_key(handler_param)
