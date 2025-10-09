from abc import ABC, abstractmethod
from typing import Optional

from v2.nacos.transport.model.internal_request import ClientDetectionRequest, \
    SetupAckRequest
from v2.nacos.transport.model.internal_response import ClientDetectionResponse, \
    SetupAckResponse
from v2.nacos.transport.model.rpc_request import Request
from v2.nacos.transport.model.rpc_response import Response
from v2.nacos.transport.rec_ability_context import RecAbilityContext


class IServerRequestHandler(ABC):

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def request_reply(self, request: Request) -> Optional[Response]:
        pass


class ClientDetectionRequestHandler(IServerRequestHandler):
    def name(self) -> str:
        return "ClientDetectionRequestHandler"

    async def request_reply(self, request: Request) -> Optional[Response]:
        if not isinstance(request, ClientDetectionRequest):
            return None

        return ClientDetectionResponse()

class SetupAckRequestHandler(IServerRequestHandler):


    def __init__(self, rec_ability_context: RecAbilityContext):
        self.rec_ability_context = rec_ability_context

    def name(self) -> str:
        return "SetupRequestHandler"

    async def request_reply(self, request: Request) -> Optional[Response]:
        if not isinstance(request, SetupAckRequest):
            return None

        if request.abilityTable:
            self.rec_ability_context.release(request.abilityTable)
        else :
            self.rec_ability_context.release({})

        return SetupAckResponse()
