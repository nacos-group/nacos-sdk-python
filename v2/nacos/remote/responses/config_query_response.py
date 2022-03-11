from typing import Optional

from v2.nacos.remote.responses import response
from v2.nacos.remote.utils import remote_response_type


class ConfigQueryResponse(response.Response):
    CONFIG_NOT_FOUND = 300
    CONFIG_QUERY_CONFLICT = 400

    content: Optional[str]
    contentType: Optional[str]
    md5: Optional[str]
    isBeta: Optional[bool]
    tag: Optional[str]
    lastModified: Optional[int]
    encryptedDataKey: Optional[str]

    def get_remote_type(self):
        return remote_response_type["ConfigQuery"]

    @staticmethod
    def build_fail_response(error_code: int, message: str):
        new_response = ConfigQueryResponse()
        new_response.set_error_info(error_code, message)
        return new_response

    @staticmethod
    def build_success_response(content: str):
        new_response = ConfigQueryResponse()
        new_response.set_contend(content)
        return new_response

    def get_tag(self) -> str:
        return self.tag

    def set_tag(self, tag: str) -> None:
        self.tag = tag

    def get_md5(self) -> str:
        return self.md5

    def set_md5(self, md5: str) -> None:
        self.md5 = md5

    def get_last_modified(self) -> int:
        return self.lastModified

    def set_last_modified(self, last_modified: int) -> None:
        self.lastModified = last_modified

    def is_beta(self) -> bool:
        return self.isBeta

    def set_beta(self, beta: bool) -> None:
        self.isBeta = beta

    def get_content(self) -> str:
        return self.content

    def set_content(self, content: str) -> None:
        self.content = content

    def get_encrypted_data_key(self) -> str:
        return self.encryptedDataKey

    def set_encrypted_data_key(self, encrypted_data_key: str) -> None:
        self.encryptedDataKey = encrypted_data_key

    def get_content_type(self) -> str:
        return self.contentType

    def set_content_type(self, content_type: str) -> None:
        self.contentType = content_type
