from abc import ABC, abstractmethod #该类需考虑兼容问题

# 加密插件服务接口
class AbstractEncryptionPluginService(ABC):
    @abstractmethod
    def encrypt(self, secret_key, content):
        pass

    @abstractmethod
    def decrypt(self, secret_key, content):
        pass

    @abstractmethod
    def generate_secret_key(self):
        pass

    @abstractmethod
    def algorithm_name(self):
        pass