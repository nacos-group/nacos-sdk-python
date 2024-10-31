from abc import ABC, abstractmethod

from pydantic import BaseModel


class Request(BaseModel, ABC):
    headers: dict = {}
    requestId: str = ''
    module: str = ''

    def put_all_headers(self, headers: dict):
        if not headers:
            return
        self.headers.update(headers)

    def put_header(self, key: str, value: str) -> None:
        self.headers[key] = value

    def clear_headers(self):
        self.headers.clear()

    def get_header(self, key: str, default_value=None) -> str:
        return self.headers[key] if self.headers[key] else default_value

    def get_headers(self) -> dict:
        return self.headers

    def get_request_id(self) -> str:
        return self.requestId

    @abstractmethod
    def get_module(self) -> str:
        pass

    @abstractmethod
    def get_request_type(self) -> str:
        pass

    def __str__(self):
        return self.__class__.__name__ + "{headers" + str(self.headers) if self.headers else "None" + ", requestId='" + \
                                                                                             self.requestId + "'}"
