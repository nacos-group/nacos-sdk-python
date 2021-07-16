from v2.nacos.remote.responses import response
from v2.nacos.remote.utils import remote_response_type


class ConnectionUnregisterResponse(response.Response):
    def get_remote_type(self):
        return remote_response_type["ConnectionUnregister"]
