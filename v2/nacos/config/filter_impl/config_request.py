from pydantic import BaseModel

from v2.nacos.config.abstract.abstract_config_context import AbstractConfigContext
from v2.nacos.config.abstract.abstract_config_request import AbstractConfigRequest
from v2.nacos.config.common.config_constants import ConfigConstants
from v2.nacos.config.filter_impl.config_context import ConfigContext


class ConfigRequest(AbstractConfigRequest, BaseModel):
    param: dict = {}
    configContext: ConfigContext = ConfigContext()

    def get_tenant(self) -> str:
        return str(self.param.get(ConfigConstants.TENANT))

    def set_tenant(self, tenant: str) -> None:
        self.param[ConfigConstants.TENANT] = tenant

    def get_data_id(self) -> str:
        return str(self.param.get(ConfigConstants.DATA_ID))

    def set_data_id(self, data_id: str) -> None:
        self.param[ConfigConstants.DATA_ID] = data_id

    def get_group(self) -> str:
        return str(self.param.get(ConfigConstants.DATA_ID))

    def set_group(self, group: str) -> None:
        self.param[ConfigConstants.GROUP] = group

    def get_content(self) -> str:
        return str(self.param.get(ConfigConstants.CONTENT))

    def set_content(self, content: str) -> None:
        self.param[ConfigConstants.CONTENT] = content

    def get_type(self) -> str:
        return str(self.param.get(ConfigConstants.TYPE))

    def set_type(self, config_type: str) -> None:
        self.param[ConfigConstants.TYPE] = config_type

    def put_parameter(self, key, value) -> None:
        self.param[key] = value

    def get_parameter(self, key) -> object:
        return self.param.get(key)

    def get_config_context(self) -> AbstractConfigContext:
        return self.configContext

    class Config:
        arbitrary_types_allowed = True
