from abc import ABCMeta, abstractmethod


class AbstractConfigFilterChain(metaclass=ABCMeta):
    @abstractmethod
    def do_filter(self, request, response) -> None:
        pass
