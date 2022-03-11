from typing import Optional

from pydantic import BaseModel

from v2.nacos.remote import utils
from v2.nacos.remote.utils import response_code
from abc import abstractmethod, ABCMeta


class Response(BaseModel, metaclass=ABCMeta):
    resultCode: int = utils.response_code["success"]
    errorCode: Optional[int]
    message: Optional[str]
    requestId: Optional[str]

    @abstractmethod
    def get_remote_type(self):
        pass

    @classmethod
    def convert(cls, obj: object):
        new_obj = cls()
        for key, value in obj.__dict__.items():
            new_obj.__dict__[key] = value
        return new_obj

    def is_success(self) -> bool:
        return self.resultCode == response_code["success"]

    def get_request_id(self) -> str:
        return self.requestId

    def set_request_id(self, request_id: str) -> None:
        self.requestId = request_id

    def get_result_code(self) -> int:
        return self.resultCode

    def set_result_code(self, result_code: int) -> None:
        self.resultCode = result_code

    def get_message(self) -> str:
        return self.message

    def set_message(self, message: str) -> None:
        self.message = message

    def set_error_code(self, error_code: int) -> None:
        self.errorCode = error_code

    def get_error_code(self) -> int:
        return self.errorCode

    def set_error_info(self, error_code: int, error_msg: str) -> None:
        self.resultCode = response_code["fail"]
        self.errorCode = error_code
        self.message = error_msg

    def __str__(self):
        return "Response{resultCode=" + str(self.resultCode) + ", errorCode=" + str(self.errorCode) + ", message='" \
                   + self.message+"'" + ", requestId='"+self.requestId + "'}"

    class Config:
        arbitrary_types_allowed = True

