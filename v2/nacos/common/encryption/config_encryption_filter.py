from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from .encryption_handler import EncryptionHandler
# 假设的ConfigRequest和ConfigResponse类
class ConfigRequest:
    def __init__(self, data_id: str, content: str, encrypted_data_key: str = ''):
        self.data_id = data_id
        self.content = content
        self.encrypted_data_key = encrypted_data_key

    def set_content(self, content: str) -> None:
        self.content = content

    def set_encrypted_data_key(self, key: str) -> None:
        self.encrypted_data_key = key

class ConfigResponse:
    def __init__(self, data_id: str, content: str, encrypted_data_key: str = ''):
        self.data_id = data_id
        self.content = content
        self.encrypted_data_key = encrypted_data_key

    def set_content(self, content: str) -> None:
        self.content = content

    def set_encrypted_data_key(self, key: str) -> None:
        self.encrypted_data_key = key


# 过滤器链接口
class IConfigFilterChain:
    @abstractmethod
    def do_filter(request: Any, response: Any) -> None:
        pass

# 过滤器接口
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

# 加密过滤器实现
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

# 假设的过滤器链实现
class ConfigFilterChain(IConfigFilterChain):
    def do_filter(self, request: Any, response: Any) -> None:
        print("Filter chain processing request and response.")

# 使用示例
if __name__ == "__main__":
    request = ConfigRequest("cipher-aes-dataId", "sensitive_data")
    response = None  # 在这个示例中，我们只处理请求
    filter_chain = ConfigFilterChain()
    encryption_filter = ConfigEncryptionFilter()
    encryption_filter.do_filter(request, response, filter_chain)
    print(f"Encrypted Content: {request.content}")
    print(f"Encrypted Data Key: {request.encrypted_data_key}")
    print("加密完成，测试解密")
    response = ConfigResponse(request.data_id, request.content, request.encrypted_data_key)
    request = None
    encryption_filter.do_filter(request, response, filter_chain)
    print(f"Encrypted Content: {response.content}")
    # print(f"Encrypted Data Key: {response.encrypted_data_key}")
    #加解密流程正常，需要适配上链
    