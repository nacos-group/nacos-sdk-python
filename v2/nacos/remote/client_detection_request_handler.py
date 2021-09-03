from v2.nacos.remote.iserver_request_handler import ServerRequestHandler
from v2.nacos.remote.requests import ClientDetectionRequest
from v2.nacos.remote.requests.request import Request
from v2.nacos.remote.responses import ClientDetectionResponse
from v2.nacos.remote.responses.response import Response


class ClientDetectionRequestHandler(ServerRequestHandler):
    def request_reply(self, request: Request) -> Response:
        if isinstance(request, ClientDetectionRequest):
            return ClientDetectionResponse()
        return
