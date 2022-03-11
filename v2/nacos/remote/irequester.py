from abc import ABCMeta, abstractmethod
from v2.nacos.remote.responses.response import Response
from v2.nacos.remote.requests.request import Request


class Requester(metaclass=ABCMeta):
    @abstractmethod
    def request(self, request: Request, timeout_mills: int) -> Response:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
