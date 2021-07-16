from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class PushAckRequest(request.Request):
    def __init__(self):
        super().__init__()
        self.__MODULE = "internal"
        self.__request_id = ""
        self.__success = False
        self.__exception = None # Exception()

    @staticmethod
    def build(request_id, success):
        new_request = PushAckRequest()
        new_request.__request_id = request_id
        new_request.__success = success
        return new_request

    def get_request_id(self):
        return self.__request_id

    def set_request_id(self, request_id):
        self.__request_id = request_id

    def is_success(self):
        return self.__success

    def set_success(self, success):
        self.__success = success

    def get_exception(self):
        return self.__exception

    def set_exception(self, exception):
        self.__exception = exception

    def get_module(self):
        return self.__MODULE

    def get_remote_type(self):
        return remote_request_type["PushAck"]
