from v2.nacos.config.encryption.encrytion_plugin_service import EncryptionPluginService
from v2.nacos.config.encryption.encrytion_plugin_manager import EncryptionPluginManager
from v2.nacos.config.encryption.encryption_handler import EncryptionHandler
import logging

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

if __name__ == "__main__":

    encryptionPluginService = EncryptionPluginService()
    EncryptionPluginManager.join(encryptionPluginService)
    handler = EncryptionHandler()
    # data_id = "cipher-AES-dataId"
    data_id = "cipher-aes-dataId"
    content = "Sensitive data"

    encrypted_key, encrypted_content = handler.encrypt_handler(
        data_id, content)
    LOGGER.info(f"Encrypted Key: {encrypted_key}")
    LOGGER.info(f"Encrypted Content: {encrypted_content}")

    decrypted_key, decrypted_content = handler.decrypt_handler(
        data_id, encrypted_key, encrypted_content)
    LOGGER.info(f"Decrypted Key: {decrypted_key}")
    LOGGER.info(f"Decrypted Content: {decrypted_content}")
