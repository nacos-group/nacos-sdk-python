from abc import ABCMeta, abstractmethod


class AbstractConfigContext(metaclass=ABCMeta):
    @abstractmethod
    def get_parameter(self, key) -> object:
        pass

    @abstractmethod
    def set_parameter(self, key, value) -> None:
        pass
