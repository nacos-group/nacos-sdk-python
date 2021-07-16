from abc import ABCMeta, abstractmethod


class ServerRequestHandler(metaclass=ABCMeta):
    @abstractmethod
    def request_reply(self, request):
        pass
