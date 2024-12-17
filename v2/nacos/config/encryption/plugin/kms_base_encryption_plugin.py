from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.config.encryption.kms_client import KmsClient
from v2.nacos.config.encryption.plugin.kms_encrytion_plugin import KmsEncryptionPlugin
from v2.nacos.config.model.config_param import HandlerParam


class KmsBaseEncryptionPlugin(KmsEncryptionPlugin):
    def __init__(self, kms_client: KmsClient):
        super().__init__(kms_client)
        self.ALGORITHM = 'cipher'

    def encrypt(self, handler_param: HandlerParam) -> HandlerParam:
        key_id = handler_param.key_id if handler_param.key_id.strip() else Constants.MSE_KMS_V1_DEFAULT_KEY_ID

        if len(handler_param.content) == 0:
            raise NacosException(INVALID_PARAM, "encrypt empty content error")
        encrypted_content = self.kms_client.encrypt(handler_param.content, key_id)
        handler_param.content = encrypted_content
        return handler_param

    def decrypt(self, handler_param: HandlerParam) -> HandlerParam:
        if len(handler_param.content) == 0:
            raise NacosException(INVALID_PARAM, "decrypt empty content error")
        plain_content = self.kms_client.decrypt(handler_param.content)
        handler_param.content = plain_content
        return handler_param

    def generate_secret_key(self, handler_param: HandlerParam) -> HandlerParam:
        return handler_param

    def algorithm_name(self):
        return self.ALGORITHM

    def encrypt_secret_key(self, handler_param: HandlerParam) -> str:
        return ""

    def decrypt_secret_key(self, handler_param: HandlerParam) -> str:
        return ""
