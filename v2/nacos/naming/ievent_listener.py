from abc import ABCMeta, abstractmethod


class EventListener(metaclass=ABCMeta):
    @abstractmethod
    def on_event(self) -> None:
        pass
