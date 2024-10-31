from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.config.encryption.abstract_encryption_plugin_service import AbstractEncryptionPluginService
from v2.nacos.config.encryption.kms_client import KmsClient
from v2.nacos.config.model.config_param import HandlerParam


class KmsBaseEncryptionPluginService(AbstractEncryptionPluginService):
    def __init__(self, kms_client: KmsClient):
        self.ALGORITHM = 'cipher-kms'
        self.kms_client = kms_client

    def key_id_param_check(self, key_id: str):
        if not key_id.strip():
            return Constants.DEFAULT_KEY_ID
        return key_id

    def encrypt(self, handler_param: HandlerParam):
        key_id = self.key_id_param_check(handler_param.key_id)
        if len(handler_param.content) == 0:
            raise NacosException(INVALID_PARAM, "encrypt empty content error")
        encrypted_content = self.kms_client.encrypt(handler_param.content, key_id)
        handler_param.content = encrypted_content

    def decrypt(self, handler_param: HandlerParam):
        if len(handler_param.content) == 0:
            raise NacosException(INVALID_PARAM, "decrypt empty content error")
        plain_content = self.kms_client.decrypt(handler_param.content)
        handler_param.content = plain_content

    def generate_secret_key(self, handler_param: HandlerParam):
        pass

    def algorithm_name(self):
        return self.ALGORITHM

    def encrypt_secret_key(self, handler_param: HandlerParam):
        pass

    def decrypt_secret_key(self, handler_param: HandlerParam):
        pass
