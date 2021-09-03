from typing import Optional

from v2.nacos.remote.responses import response
from v2.nacos.remote.utils import remote_response_type


class ServerCheckResponse(response.Response):
    connectionId: Optional[str]

    def get_remote_type(self):
        return remote_response_type["ServerCheck"]

    def set_connection_id(self, connection_id: str) -> None:
        self.connectionId = connection_id

    def get_connection_id(self) -> str:
        return self.connectionId
