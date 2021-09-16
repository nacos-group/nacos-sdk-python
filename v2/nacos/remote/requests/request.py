from abc import abstractmethod, ABCMeta
from typing import Optional

from pydantic import BaseModel


class Request(BaseModel, metaclass=ABCMeta):
    headers: dict = {}
    requestId: Optional[str]
    module: Optional[str]

    def put_header(self, key: str, value: str) -> None:
        self.headers[key] = value

    def put_all_header(self, headers: dict) -> None:
        if not headers:
            return
        self.headers.update(headers)

    def get_header(self, key: str, default_value=None) -> str:
        return self.headers[key] if self.headers[key] else default_value

    def get_request_id(self) -> str:
        return self.requestId

    def set_request_id(self, request_id: str) -> None:
        self.requestId = request_id

    @abstractmethod
    def get_module(self) -> str:
        pass

    @abstractmethod
    def get_remote_type(self) -> str:
        pass

    def get_headers(self) -> dict:
        return self.headers

    def clear_headers(self) -> None:
        self.headers.clear()

    def __str__(self):
        return self.__class__.__name__ + "{headers" + str(self.headers) if self.headers else "None" + ", requestId='" +\
                                                                                             self.requestId + "'}"

    @classmethod
    def convert(cls, obj: object):
        new_obj = cls()
        for key, value in obj.__dict__.items():
            new_obj.__dict__[key] = value
        return new_obj

    class Config:
        arbitrary_types_allowed = True
