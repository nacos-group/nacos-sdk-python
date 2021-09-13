from abc import ABCMeta, abstractmethod


class AbstractFilterConfig(metaclass=ABCMeta):
    @abstractmethod
    def get_filter_name(self) -> str:
        pass

    @abstractmethod
    def get_init_parameter(self, name: str) -> object:
        pass
