from v2.nacos.remote.utils import response_code
from abc import abstractmethod


class Response:
    def __init__(self):
        self.result_code = response_code["success"]
        self.error_code = None
        self.message = None
        self.request_id = None

    def is_success(self) -> bool:
        return self.result_code == response_code["success"]

    def get_request_id(self) -> str:
        return self.request_id

    def set_request_id(self, request_id: str) -> None:
        self.request_id = request_id

    def get_result_code(self) -> int:
        return self.result_code

    def set_result_code(self, result_code: int) -> None:
        self.result_code = result_code

    def get_message(self) -> str:
        return self.message

    def set_message(self, message: str) -> None:
        self.message = message

    def set_error_code(self, error_code: int) -> None:
        self.error_code = error_code

    def get_error_code(self) -> int:
        return self.error_code

    def set_error_info(self, error_code: int, error_msg: str) -> None:
        self.result_code = response_code["fail"]
        self.error_code = error_code
        self.message = error_msg

    @abstractmethod
    def get_remote_type(self):
        pass

    def __str__(self):
        return "Response{resultCode=" + str(self.result_code) + ", errorCode=" + str(self.error_code) + ", message='" \
               + self.message+"'" + ", requestId='"+self.request_id + "'}"

    @classmethod
    def convert(cls, obj: object):
        new_obj = cls()
        for key, value in obj.__dict__.items():
            new_obj.__dict__[key] = value
        return new_obj
