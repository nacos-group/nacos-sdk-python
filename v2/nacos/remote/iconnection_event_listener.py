from abc import ABCMeta, abstractmethod


class ConnectionEventListener(metaclass=ABCMeta):
    @abstractmethod
    def on_connected(self) -> None:
        pass

    @abstractmethod
    def on_disconnect(self) -> None:
        pass
