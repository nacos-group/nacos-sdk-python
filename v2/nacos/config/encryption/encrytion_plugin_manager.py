import logging
from threading import Lock
from v2.nacos.config.encryption.encrytion_plugin_service import EncryptionPluginService



class EncryptionPluginManager:

    def __init__(self):
        self.ENCRYPTION_SPI_MAP = {}
        self._lock = Lock()
        self.load_initial()

    def load_initial(self):
        encryptionPluginService = EncryptionPluginService()
        encryption_plugin_services = NacosServiceLoader.load(
            encryptionPluginService)
        for service in encryption_plugin_services:
            algorithm_name = service.algorithm_name()
            if not algorithm_name:
                LOGGER.warn(
                    f"Load EncryptionPluginService {service.__class__.__name__} failed: algorithmName is missing."
                )
                continue
            with self._lock:
                self.ENCRYPTION_SPI_MAP[algorithm_name] = service
                LOGGER.info(
                    f"Load EncryptionPluginService {service.__class__.__name__} with algorithmName {algorithm_name} successfully."
                )

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
            instance.ENCRYPTION_SPI_MAP[
                encryption_plugin_service.algorithm_name(
                )] = encryption_plugin_service
            LOGGER.info("[EncryptionPluginManager] join successfully.")
            print(instance.ENCRYPTION_SPI_MAP)
