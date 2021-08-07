from v2.nacos.remote.responses import response
from v2.nacos.remote.utils import remote_response_type


class ServerCheckResponse(response.Response):
    def __init__(self):
        self.connection_id = ""

    def get_connection_id(self) -> str:
        return self.connection_id

    def set_connection_id(self, connection_id) -> None:
        self.connection_id = connection_id

    def get_remote_type(self):
        return remote_response_type["ServerCheck"]
