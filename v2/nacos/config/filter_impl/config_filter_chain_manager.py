from threading import RLock

from v2.nacos.common.utils import synchronized_with_attr
from v2.nacos.config.abstract.abstract_config_filter_chain import AbstractConfigFilterChain


class ConfigFilterChainManager(AbstractConfigFilterChain):
    def __init__(self):
        self.filters = []
        self.lock = RLock()

    @synchronized_with_attr("lock")
    def add_filter(self, config_filter):
        i = 0
        while i < len(self.filters):
            current_value = self.filters[i]
            if current_value.get_filter_name == config_filter.get_filter_name():
                break
            if config_filter.get_order() >= current_value.get_order() and i < len(self.filters):
                i = i + 1
            else:
                self.filters.insert(i, config_filter)
                break

        if i == len(self.filters):
            self.filters.insert(i, config_filter)

        return self

    def do_filter(self, request, response) -> None:
        ConfigFilterChainManager.VirtualFilterChain(self.filters).do_filter(request, response)

    class VirtualFilterChain(AbstractConfigFilterChain):
        def __init__(self, additional_filters: list):
            self.additional_filters = additional_filters
            self.current_position = 0

        def do_filter(self, request, response) -> None:
            if self.current_position != len(self.additional_filters):
                self.current_position = self.current_position + 1
                next_filter = self.additional_filters[self.current_position - 1]
                next_filter.do_filter(request, response, self)
