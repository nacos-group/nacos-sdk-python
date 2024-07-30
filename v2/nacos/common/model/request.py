from typing import Dict
from abc import ABC, abstractmethod
from v2.nacos.utils.common_util import to_json_string


class Request:

    def __init__(self):
        self._headers: Dict[str, str] = {}
        self._request_id: str = ""

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        self._headers = value

    @property
    def request_id(self):
        return self._request_id

    @request_id.setter
    def request_id(self, value):
        self._request_id = value

    def put_all_headers(self, headers: Dict[str, str]):
        self._headers.update(headers)

    def clear_headers(self):
        self._headers.clear()

    def get_headers(self) -> Dict[str, str]:
        return self._headers

    def get_body(self) -> str:
        return to_json_string(self.__dict__)

    def get_request_id(self) -> str:
        return self._request_id

    def get_string_to_sign(self) -> str:
        return ""


class IRequest(ABC):

    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        pass

    @abstractmethod
    def get_request_type(self) -> str:
        pass

    @abstractmethod
    def get_body(self) -> str:
        pass

    @abstractmethod
    def put_all_headers(self, headers: Dict[str, str]):
        pass

    @abstractmethod
    def get_request_id(self) -> str:
        pass

    @abstractmethod
    def get_string_to_sign(self) -> str:
        pass
