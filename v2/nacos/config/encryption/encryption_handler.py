from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM, NOT_FOUND
from v2.nacos.config.encryption.encrytion_plugin_manager import EncryptionPluginManager
from v2.nacos.config.model.config_param import HandlerParam


class EncryptionHandler:

    @staticmethod
    def check_cipher(data_id: str) -> bool:
        return data_id.startswith(Constants.CIPHER_PRE_FIX) and not data_id == Constants.CIPHER_PRE_FIX

    @staticmethod
    def encrypt_handler(handler_param: HandlerParam):
        if not EncryptionHandler.check_cipher(handler_param.data_id):
            raise NacosException(INVALID_PARAM, "the prefix of data_id must be cipher when encrypting.")

        manager = EncryptionPluginManager.get_instance()
        service = manager.find_encryption_service(handler_param.data_id)
        if not service:
            raise NacosException(NOT_FOUND, f"encryption plugin service not found, data_id:{handler_param.data_id}")

        service.generate_secret_key(handler_param)
        service.encrypt(handler_param)
        service.encrypt_secret_key(handler_param)

    @staticmethod
    def decrypt_handler(handler_param: HandlerParam):
        if not EncryptionHandler.check_cipher(handler_param.data_id):
            raise NacosException(INVALID_PARAM, "the prefix of data_id must be cipher when decrypting.")

        manager = EncryptionPluginManager.get_instance()
        service = manager.find_encryption_service(handler_param.data_id)
        if not service:
            raise NacosException(NOT_FOUND, f"encryption plugin service not found, data_id:{handler_param.data_id}")

        service.decrypt_secret_key(handler_param)
        service.decrypt(handler_param)
