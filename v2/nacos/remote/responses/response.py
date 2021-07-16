from v2.nacos.remote.utils import response_code
from abc import abstractmethod


class Response:
    def __init__(self):
        self.result_code = response_code["success"]
        self.error_code = None
        self.message = None
        self.request_id = None

    def is_success(self):
        return self.result_code == response_code["success"]

    def get_request_id(self):
        return self.request_id

    def set_request_id(self, request_id):
        self.request_id = request_id

    def is_success(self):
        return self.result_code == response_code["success"]

    def get_result_code(self):
        return self.result_code

    def set_result_code(self, result_code):
        self.result_code = result_code

    def get_message(self):
        return self.message

    def set_message(self, message):
        self.message = message

    def set_error_code(self, error_code):
        self.error_code = error_code

    def set_error_info(self, error_code, error_msg):
        self.result_code = response_code["fail"]
        self.error_code = error_code
        self.message = error_msg

    @abstractmethod
    def get_remote_type(self):
        pass

    def __str__(self):
        return "Response{resultCode=" + str(self.result_code) + ", errorCode=" + str(self.error_code) + ", message='" \
               + self.message+"'" + ", requestId='"+self.request_id + "'}"
