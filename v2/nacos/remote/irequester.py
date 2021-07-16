from abc import ABCMeta, abstractmethod


class Requester(metaclass=ABCMeta):
    @abstractmethod
    def request(self, request, timeout_mills):
        pass

    @abstractmethod
    def request_future(self, request):
        pass

    @abstractmethod
    def async_request(self, request, request_callback):
        pass

    @abstractmethod
    def close(self):
        pass
