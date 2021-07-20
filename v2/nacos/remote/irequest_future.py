from abc import ABCMeta, abstractmethod
from v2.nacos.remote.responses.response import Response


class RequestFuture(metaclass=ABCMeta):
    @abstractmethod
    def is_done(self) -> bool:
        pass

    @abstractmethod
    def get(self) -> Response:
        pass

    @abstractmethod
    def get(self, timeout: int) -> Response:
        pass
