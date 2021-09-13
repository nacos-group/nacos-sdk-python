from abc import ABCMeta, abstractmethod

from v2.nacos.config.abstract.abstract_config_context import AbstractConfigContext


class AbstractConfigRequest(metaclass=ABCMeta):
    @abstractmethod
    def put_parameter(self, key, value) -> None:
        pass

    @abstractmethod
    def get_parameter(self, key) -> object:
        pass

    @abstractmethod
    def get_config_context(self) -> AbstractConfigContext:
        pass
