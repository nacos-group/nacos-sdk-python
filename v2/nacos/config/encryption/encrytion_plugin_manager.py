from threading import Lock

from v2.nacos.config.encryption.abstract_encryption_plugin_service import AbstractEncryptionPluginService


class EncryptionPluginManager:
    _instance = None
    ENCRYPTION_SPI_MAP = {}
    _lock = Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = EncryptionPluginManager()
        return cls._instance

    def find_encryption_service(self, data_id: str):
        for algorithm_name in self.ENCRYPTION_SPI_MAP:
            if data_id.startswith(algorithm_name):
                return self.ENCRYPTION_SPI_MAP[algorithm_name]
        return None

    @staticmethod
    def join(encryption_plugin_service: AbstractEncryptionPluginService):
        if not encryption_plugin_service:
            return
        instance = EncryptionPluginManager.get_instance()
        with instance._lock:
            instance.ENCRYPTION_SPI_MAP[
                encryption_plugin_service.algorithm_name(
                )] = encryption_plugin_service
