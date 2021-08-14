from v2.nacos.remote.responses import response
from v2.nacos.remote.utils import remote_response_type


class ServiceListResponse(response.Response):
    def __init__(self):
        super().__init__()
        self.count = 0
        self.service_name = []

    def get_remote_type(self):
        return remote_response_type["ServiceList"]
