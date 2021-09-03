from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class HealthCheckRequest(request.Request):
    def get_module(self) -> str:
        return "internal"

    def get_remote_type(self) -> str:
        return remote_request_type["HealthCheck"]