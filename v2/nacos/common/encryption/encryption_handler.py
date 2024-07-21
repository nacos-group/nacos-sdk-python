import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from .encryption_plugin_manager import EncryptionPluginManager
# 设置日志配置
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# 加密处理器
class EncryptionHandler:
    PREFIX = "cipher-"

    @staticmethod
    def check_cipher(data_id: str) -> bool:
        return data_id.startswith(EncryptionHandler.PREFIX) and not data_id == EncryptionHandler.PREFIX

    @staticmethod
    def parse_algorithm_name(data_id: str) -> Optional[str]:
        parts = data_id.split("-")
        return parts[1] if len(parts) > 1 else None

    @staticmethod
    def encrypt_handler(data_id: str, content: str) -> Tuple[str, str]:
        if not EncryptionHandler.check_cipher(data_id):
            return "", content

        algorithm_name = EncryptionHandler.parse_algorithm_name(data_id)
        if not algorithm_name:
            LOGGER.warn(f"[EncryptionHandler] [encryptHandler] No algorithm name found in dataId: {data_id}")
            return "", content

        manager = EncryptionPluginManager.get_instance()
        service = manager.find_encryption_service(algorithm_name)
        if not service:
            LOGGER.warn(f"[EncryptionHandler] [encryptHandler] No encryption service found for algorithm name: {algorithm_name}")
            return "", content

        secret_key = service.generate_secret_key()
        encrypt_content = service.encrypt(secret_key, content)
        return service.encrypt_secret_key(secret_key), encrypt_content

    @staticmethod
    def decrypt_handler(data_id: str, secret_key: str, content: str) -> Tuple[str, str]:
        if not EncryptionHandler.check_cipher(data_id):
            return secret_key, content

        algorithm_name = EncryptionHandler.parse_algorithm_name(data_id)
        if not algorithm_name:
            LOGGER.warn(f"[EncryptionHandler] [decryptHandler] No algorithm name found in dataId: {data_id}")
            return secret_key, content

        manager = EncryptionPluginManager.get_instance()
        service = manager.find_encryption_service(algorithm_name)
        if not service:
            LOGGER.warn(f"[EncryptionHandler] [decryptHandler] No encryption service found for algorithm name: {algorithm_name}")
            return secret_key, content

        decrypt_secret_key = service.decrypt_secret_key(secret_key)
        decrypt_content = service.decrypt(decrypt_secret_key, content)
        return decrypt_secret_key, decrypt_content

# 使用示例
if __name__ == "__main__":
    handler = EncryptionHandler()
    # data_id = "cipher-AES-dataId"
    data_id = "cipher-aes-dataId" #这里目前只支持小写模式
    content = "Sensitive data"

    encrypted_key, encrypted_content = handler.encrypt_handler(data_id, content)
    LOGGER.info(f"Encrypted Key: {encrypted_key}")
    LOGGER.info(f"Encrypted Content: {encrypted_content}")

    decrypted_key, decrypted_content = handler.decrypt_handler(data_id, encrypted_key, encrypted_content)
    LOGGER.info(f"Decrypted Key: {decrypted_key}")
    LOGGER.info(f"Decrypted Content: {decrypted_content}")