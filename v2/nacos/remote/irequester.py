from abc import ABCMeta, abstractmethod
from v2.nacos.remote.responses.response import Response
from v2.nacos.remote.requests.request import Request
from v2.nacos.remote.irequest_future import RequestFuture
from v2.nacos.remote.irequest_callback import RequestCallBack


class Requester(metaclass=ABCMeta):
    @abstractmethod
    def request(self, request: Request, timeout_mills: int) -> Response:
        pass

    # @abstractmethod
    # def request_future(self, request: Request) -> RequestFuture:
    #     pass
    #
    # @abstractmethod
    # def async_request(self, request: Request, request_callback: RequestCallBack) -> None:
    #     pass

    @abstractmethod
    def close(self) -> None:
        pass
