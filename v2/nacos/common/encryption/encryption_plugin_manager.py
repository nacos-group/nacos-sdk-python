import logging
from threading import Lock #这里考虑是用这个lock还是用concurrent.futures实现一个
#测试导入
from .encryption_plugin_service import EncryptionPluginService

# 设置日志配置
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# 服务加载器
class NacosServiceLoader:
    @staticmethod
    def load(service_class):
        # 这里应该加载实现 service_class 接口的所有服务
        # 示例中我们只返回一个示例加密插件服务
        return [service_class]

# 加密插件管理器
class EncryptionPluginManager:
    def __init__(self):
        self.ENCRYPTION_SPI_MAP = {}
        self._lock = Lock()
        self.load_initial()

    def load_initial(self):
        encryptionPluginService = EncryptionPluginService()  #这里是一个测试形式的服务插入,需要适配
        encryption_plugin_services = NacosServiceLoader.load(encryptionPluginService)  #这里需要改
        # encryption_plugin_services = []
        for service in encryption_plugin_services:
            algorithm_name = service.algorithm_name()
            if not algorithm_name:
                LOGGER.warn(f"Load EncryptionPluginService {service.__class__.__name__} failed: algorithmName is missing.")
                continue
            with self._lock:
                self.ENCRYPTION_SPI_MAP[algorithm_name] = service
                LOGGER.info(f"Load EncryptionPluginService {service.__class__.__name__} with algorithmName {algorithm_name} successfully.")

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance") or cls._instance is None:
            cls._instance = EncryptionPluginManager()
        return cls._instance

    def find_encryption_service(self, algorithm_name):
        return self.ENCRYPTION_SPI_MAP.get(algorithm_name)

    @staticmethod
    def join(encryption_plugin_service):
        if not encryption_plugin_service:
            return
        instance = EncryptionPluginManager.get_instance()
        with instance._lock:
            instance.ENCRYPTION_SPI_MAP[encryption_plugin_service.algorithm_name()] = encryption_plugin_service
            LOGGER.info("[EncryptionPluginManager] join successfully.")
            print(instance.ENCRYPTION_SPI_MAP)

# 使用示例
if __name__ == "__main__":
    manager = EncryptionPluginManager.get_instance()
    service = manager.find_encryption_service('AES')
    if service:
        secret_key = service.generate_secret_key()
        encrypted_content = service.encrypt(secret_key, 'Sensitive data')
        LOGGER.info(f'Encrypted: {encrypted_content}')
        decrypted_content = service.decrypt(secret_key, encrypted_content)
        LOGGER.info(f'Decrypted: {decrypted_content}')

        # 密钥加密和解密操作
        encrypted_secret_key = service.encrypt_secret_key(secret_key)
        LOGGER.info(f"Encrypted Secret Key: {encrypted_secret_key}")
        decrypted_secret_key = service.decrypt_secret_key(encrypted_secret_key)
        LOGGER.info(f"Decrypted Secret Key: {decrypted_secret_key}")