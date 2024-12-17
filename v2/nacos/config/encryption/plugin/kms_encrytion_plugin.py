from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.config.encryption.plugin.encryption_plugin import EncryptionPlugin
from v2.nacos.config.encryption.kms_client import KmsClient
from v2.nacos.config.model.config_param import HandlerParam
from v2.nacos.utils import aes_util
from v2.nacos.utils.encode_util import decode_base64, str_to_bytes


class KmsEncryptionPlugin(EncryptionPlugin):
    def __init__(self, kms_client: KmsClient):
        self.ALGORITHM = 'cipher-kms'
        self.kms_client = kms_client

    @staticmethod
    def param_check(handler_param: HandlerParam):
        if not handler_param.plain_data_key.strip():
            raise NacosException(INVALID_PARAM, "empty plain_data_key error")
        if not handler_param.content.strip():
            raise NacosException(INVALID_PARAM, "encrypt empty content error")

    def encrypt(self, handler_param: HandlerParam) -> HandlerParam:
        self.param_check(handler_param)
        handler_param.content = aes_util.encrypt(
            key=handler_param.plain_data_key,
            message=handler_param.content)
        return handler_param

    def decrypt(self, handler_param: HandlerParam) -> HandlerParam:
        self.param_check(handler_param)
        handler_param.content = aes_util.decrypt(
            key=handler_param.plain_data_key,
            encr_data=handler_param.content)
        return handler_param

    def generate_secret_key(self, handler_param: HandlerParam) -> HandlerParam:
        pass

    def algorithm_name(self):
        pass

    def encrypt_secret_key(self, handler_param: HandlerParam) -> str:
        key_id = handler_param.key_id if handler_param.key_id.strip() else Constants.MSE_KMS_V1_DEFAULT_KEY_ID
        if len(handler_param.plain_data_key) == 0:
            raise NacosException(INVALID_PARAM, "empty plain_data_key error")
        return self.kms_client.encrypt(handler_param.plain_data_key, key_id)

    def decrypt_secret_key(self, handler_param: HandlerParam) -> str:
        if len(handler_param.encrypted_data_key) == 0:
            raise NacosException(INVALID_PARAM, "empty encrypted data key error")
        return self.kms_client.decrypt(handler_param.encrypted_data_key)
