from abc import ABCMeta, abstractmethod


class RequestFuture(metaclass=ABCMeta):
    @abstractmethod
    def is_done(self):
        pass

    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def get(self, timeout):
        pass
