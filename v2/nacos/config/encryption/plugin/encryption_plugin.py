from abc import ABC, abstractmethod

from v2.nacos.config.model.config_param import HandlerParam


class EncryptionPlugin(ABC):

    @abstractmethod
    def encrypt(self, handler_param: HandlerParam) -> HandlerParam:
        pass

    @abstractmethod
    def decrypt(self, handler_param: HandlerParam) -> HandlerParam:
        pass

    @abstractmethod
    def generate_secret_key(self, handler_param: HandlerParam) -> HandlerParam:
        pass

    @abstractmethod
    def algorithm_name(self):
        pass

    @abstractmethod
    def encrypt_secret_key(self, handler_param: HandlerParam) -> str:
        pass

    @abstractmethod
    def decrypt_secret_key(self, handler_param: HandlerParam) -> str:
        pass
