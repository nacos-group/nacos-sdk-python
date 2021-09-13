from pydantic import BaseModel

from v2.nacos.config.abstract.abstract_config_response import AbstractConfigResponse
from v2.nacos.config.common.config_constants import ConfigConstants
from v2.nacos.config.filter_impl.config_context import ConfigContext


class ConfigResponse(AbstractConfigResponse, BaseModel):
    param: dict = {}
    configContext: ConfigContext = ConfigContext()

    def get_tenant(self) -> str:
        return self.param.get(ConfigConstants.TENANT)

    def set_tenant(self, tenant: str) -> None:
        self.param[ConfigConstants.TENANT] = tenant

    def get_data_id(self) -> str:
        return self.param.get(ConfigConstants.DATA_ID)

    def set_data_id(self, data_id: str) -> None:
        self.param[ConfigConstants.DATA_ID] = data_id

    def get_group(self) -> str:
        return self.param.get(ConfigConstants.CONTENT)

    def set_group(self, content) -> None:
        self.param[ConfigConstants.CONTENT] = content

    def get_content(self) -> str:
        return self.param.get(ConfigConstants.CONTENT)

    def set_content(self, content) -> None:
        self.param[ConfigConstants.CONTENT] = content

    def get_config_type(self) -> str:
        return self.param.get(ConfigConstants.CONFIG_TYPE)

    def set_config_type(self, config_type: str) -> None:
        self.param[ConfigConstants.CONFIG_TYPE] = config_type

    def get_encrypted_data_key(self) -> str:
        return self.param.get(ConfigConstants.ENCRYPTED_DATA_KEY)

    def set_encrypted_data_key(self, encrypted_data_key: str) -> None:
        self.param[ConfigConstants.ENCRYPTED_DATA_KEY] = encrypted_data_key

    def get_parameter(self, key: str):
        return self.param.get(key)

    def put_parameter(self, key: str, value):
        self.param[key] = value

    def get_config_context(self) -> ConfigContext:
        return self.configContext

    class Config:
        arbitrary_types_allowed = True
