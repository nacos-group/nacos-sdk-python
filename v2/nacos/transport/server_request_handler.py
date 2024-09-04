from abc import ABC, abstractmethod
from typing import Optional

from v2.nacos.transport.model.internal_request import ClientDetectionRequest
from v2.nacos.transport.model.internal_response import ClientDetectionResponse
from v2.nacos.transport.model.rpc_request import Request
from v2.nacos.transport.model.rpc_response import Response


class IServerRequestHandler(ABC):

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def request_reply(self, request: Request) -> Optional[Response]:
        pass


class ClientDetectionRequestHandler(IServerRequestHandler):
    def name(self) -> str:
        return "ClientDetectionRequestHandler"

    def request_reply(self, request) -> Optional[Response]:
        if isinstance(request, ClientDetectionRequest):
            return ClientDetectionResponse()
        return None
