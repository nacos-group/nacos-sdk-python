from abc import ABCMeta, abstractmethod


class Poller(metaclass=ABCMeta):
    @abstractmethod
    def next(self):
        pass

    @abstractmethod
    def refresh(self, items: list):
        pass
