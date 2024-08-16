from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from v2.nacos.config.encryption.encryption_handler import EncryptionHandler


class IConfigFilterChain:
    @abstractmethod
    def do_filter(request: Any, response: Any) -> None:
        pass


class IConfigFilter(ABC):
    @abstractmethod
    def init(self, properties: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def do_filter(self, request: Any, response: Any, filter_chain: IConfigFilterChain) -> None:
        pass

    @abstractmethod
    def get_order(self) -> int:
        pass

    @abstractmethod
    def get_filter_name(self) -> str:
        pass


class ConfigEncryptionFilter(IConfigFilter):

    def init(self) -> None:
        pass

    def do_filter(self, request: Any, response: Any, filter_chain: IConfigFilterChain) -> None:
        if request and isinstance(request, ConfigRequest) and not response:
            data_id = request.data_id
            content = request.content
            secret_key, encrypt_content = EncryptionHandler.encrypt_handler(data_id, content)
            if encrypt_content:
                request.set_content(encrypt_content)
            if secret_key:
                request.set_encrypted_data_key(secret_key)

        if response and isinstance(response, ConfigResponse) and not request:
            data_id = response.data_id
            encrypted_data_key = response.encrypted_data_key
            content = response.content
            secret_key, decrypt_content = EncryptionHandler.decrypt_handler(data_id, encrypted_data_key, content)
            if decrypt_content:
                response.set_content(decrypt_content)
            if secret_key:
                response.set_encrypted_data_key(secret_key)

        filter_chain.do_filter(request, response)

    def get_order(self) -> int:
        return 0

    def get_filter_name(self) -> str:
        return self.__class__.__name__


