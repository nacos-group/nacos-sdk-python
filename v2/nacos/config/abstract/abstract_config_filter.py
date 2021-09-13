from abc import ABCMeta, abstractmethod


class AbstractConfigFilter(metaclass=ABCMeta):
    @abstractmethod
    def init(self, filter_config) -> None:
        pass

    @abstractmethod
    def do_filter(self, request, response, filter_chain) -> None:
        pass

    @abstractmethod
    def get_order(self) -> int:
        pass

    @abstractmethod
    def get_filter_name(self) -> str:
        pass
