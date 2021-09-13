from abc import ABCMeta, abstractmethod
from typing import Optional

from v2.nacos.remote.responses.response import Response
from v2.nacos.remote.requests.request import Request


class ServerRequestHandler(metaclass=ABCMeta):
    @abstractmethod
    def request_reply(self, request: Request) -> Optional[Response]:
        pass
