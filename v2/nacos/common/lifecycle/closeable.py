from abc import ABCMeta, abstractmethod


class Closeable(metaclass=ABCMeta):
    @abstractmethod
    def shutdown(self) -> None:
        pass
