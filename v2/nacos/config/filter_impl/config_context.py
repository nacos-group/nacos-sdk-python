from v2.nacos.config.abstract.abstract_config_context import AbstractConfigContext


class ConfigContext(AbstractConfigContext):
    def __init__(self):
        self.param = {}

    def get_parameter(self, key) -> object:
        return self.param.get(key)

    def set_parameter(self, key, value) -> None:
        self.param[key] = value

