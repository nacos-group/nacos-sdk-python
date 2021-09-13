from typing import Optional

from v2.nacos.remote.iserver_request_handler import ServerRequestHandler
from v2.nacos.remote.requests.client_detection_request import ClientDetectionRequest
from v2.nacos.remote.requests.request import Request
from v2.nacos.remote.responses.client_detection_response import ClientDetectionResponse
from v2.nacos.remote.responses.response import Response


class ClientDetectionRequestHandler(ServerRequestHandler):
    def request_reply(self, request: Request) -> Optional[Response]:
        if isinstance(request, ClientDetectionRequest):
            return ClientDetectionResponse()
        return
