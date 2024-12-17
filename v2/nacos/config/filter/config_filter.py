from abc import ABC, abstractmethod
from typing import List

from v2.nacos.config.model.config_param import ConfigParam


class IConfigFilter(ABC):
    @abstractmethod
    def do_filter(self, config_param):
        pass

    @abstractmethod
    def get_order(self):
        pass

    @abstractmethod
    def get_filter_name(self):
        pass


class ConfigFilterChainManager:
    def __init__(self):
        self.config_filters = []

    def add_filter(self, conf_filter: IConfigFilter) -> None:
        for existing_filter in self.config_filters:
            if conf_filter.get_filter_name() == existing_filter.get_filter_name():
                return
        for i, existing_filter in enumerate(self.config_filters):
            if conf_filter.get_order() < existing_filter.get_order():
                self.config_filters.insert(i, conf_filter)
                return
        self.config_filters.append(conf_filter)

    def get_filters(self) -> List[IConfigFilter]:
        return self.config_filters

    def do_filters(self, param: ConfigParam) -> None:
        for config_filter in self.config_filters:
            config_filter.do_filter(param)

    def do_filter_by_name(self, param: ConfigParam, name: str) -> None:
        for config_filter in self.config_filters:
            if config_filter.get_filter_name() == name:
                config_filter.do_filter(param)
                return
        raise ValueError(f"Cannot find the filter with name {name}")