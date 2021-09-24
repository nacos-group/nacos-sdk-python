from abc import ABCMeta, abstractmethod

from v2.nacos.naming.utils.ievent import Event


class EventListener(metaclass=ABCMeta):
    @abstractmethod
    def on_event(self, event: Event) -> None:
        pass
