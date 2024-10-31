from abc import ABC, abstractmethod

from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.config.encryption.abstract_encryption_plugin_service import AbstractEncryptionPluginService
from v2.nacos.config.encryption.kms_client import KmsClient
from v2.nacos.config.model.config_param import HandlerParam
from v2.nacos.utils import aes_util, encode_util


class KmsAesEncryptionPluginService(AbstractEncryptionPluginService, ABC):
    def __init__(self, kms_client: KmsClient):
        self.kms_client = kms_client

    def key_id_param_check(self, key_id: str):
        if not key_id.strip():
            return Constants.DEFAULT_KEY_ID
        return key_id

    def param_check(self, handler_param: HandlerParam):
        if len(handler_param.plain_data_key) == 0:
            raise NacosException(INVALID_PARAM, "empty plain_data_key error")
        if len(handler_param.content) == 0:
            raise NacosException(INVALID_PARAM, "encrypt empty content error")

    def encrypt(self, handler_param: HandlerParam):
        self.param_check(handler_param)
        encrypted_bytes = aes_util.encrypt_to_bytes(
            encode_util.decode_string_to_utf8_bytes(handler_param.plain_data_key),
            encode_util.decode_string_to_utf8_bytes(handler_param.content))
        handler_param.content = encode_util.encode_base64(encrypted_bytes)

    def decrypt(self, handler_param: HandlerParam):
        self.param_check(handler_param)
        decrypted_bytes = aes_util.decrypt_to_bytes(
            encode_util.decode_string_to_utf8_bytes(handler_param.plain_data_key),
            encode_util.decode_base64(handler_param.content))
        handler_param.content = encode_util.encode_utf8_bytes_to_string(decrypted_bytes)

    @abstractmethod
    def generate_secret_key(self, handler_param: HandlerParam):
        pass

    @abstractmethod
    def algorithm_name(self):
        pass

    def encrypt_secret_key(self, handler_param: HandlerParam):
        key_id = self.key_id_param_check(handler_param.key_id)
        if len(handler_param.plain_data_key) == 0:
            raise NacosException(INVALID_PARAM, "empty plain_data_key error")
        encrypted_data_key = self.kms_client.encrypt(handler_param.plain_data_key, key_id)
        handler_param.encrypted_data_key = encrypted_data_key

    def decrypt_secret_key(self, handler_param: HandlerParam):
        if len(handler_param.encrypted_data_key) == 0:
            raise NacosException(INVALID_PARAM, "empty encrypted data key error")
        plain_data_key = self.kms_client.decrypt(handler_param.encrypted_data_key)
        handler_param.plain_data_key = plain_data_key
