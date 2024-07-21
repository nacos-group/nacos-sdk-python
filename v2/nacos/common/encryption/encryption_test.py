from .encryption_plugin_service import EncryptionPluginService
from .encryption_plugin_manager import EncryptionPluginManager
from .encryption_handler import EncryptionHandler
import logging
# 设置日志配置
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


if __name__ == "__main__":
# 使用示例
    pass
    encryptionPluginService = EncryptionPluginService()
    EncryptionPluginManager.join(encryptionPluginService) #这里测试不初始化load_initial，直接join服务
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