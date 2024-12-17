from abc import ABC, abstractmethod

from pydantic import BaseModel


class Response(BaseModel, ABC):
    resultCode: int = 200
    errorCode: int = 0
    message: str = ''
    requestId: str = ''

    @classmethod
    def convert(cls, obj: object):
        new_obj = cls()
        for key, value in obj.__dict__.items():
            new_obj.__dict__[key] = value
        return new_obj

    def set_request_id(self, request_id: str):
        self.requestId = request_id

    def is_success(self) -> bool:
        return self.errorCode == 0

    def get_error_code(self) -> int:
        return self.errorCode

    def get_result_code(self) -> int:
        return self.resultCode

    def get_message(self) -> str:
        return self.message

    def __str__(self):
        return "Response{resultCode=" + str(self.resultCode) + ", errorCode=" + str(self.errorCode) + ", message='" \
            + self.message + "'" + ", requestId='" + self.requestId + "'}"

    @abstractmethod
    def get_response_type(self) -> str:
        pass
