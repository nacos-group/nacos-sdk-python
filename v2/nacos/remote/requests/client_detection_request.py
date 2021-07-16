from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class ClientDetectionRequest(request.Request):
    def __init__(self):
        super().__init__()
        self.__MODULE = "internal"

    def get_module(self):
        return self.__MODULE

    def get_remote_type(self):
        return remote_request_type["ClientDetection"]
