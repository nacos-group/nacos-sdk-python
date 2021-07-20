from v2.nacos.remote.responses import response
from v2.nacos.remote.utils import remote_response_type, response_code


class ConfigChangeBatchListenResponse(response.Response):
    def __init__(self):
        super().__init__()
        self.changed_configs = []

    def get_remote_type(self):
        return remote_response_type["ConfigChangeBatchListen"]

    def add_change_config(self, data_id: str, group: str, tenant: str) -> None:
        config_context = ConfigChangeBatchListenResponse.ConfigContext()
        config_context.data_id = data_id
        config_context.group = group
        config_context.tenant = tenant
        self.changed_configs.append(config_context)

    def get_changed_configs(self) -> list:
        return self.changed_configs

    def set_changed_configs(self, changed_configs: list) -> None:
        self.changed_configs = changed_configs

    @staticmethod
    def build_fail_response(error_message: str):
        new_response = ConfigChangeBatchListenResponse()
        new_response.set_result_code(response_code["fail"])
        new_response.set_message(error_message)
        return new_response

    class ConfigContext:
        def __init__(self):
            self.group = ""
            self.data_id = ""
            self.tenant = ""

        def __str__(self):
            return "ConfigContext{group='" + self.group + "', dataId='" + self.data_id + "', tenant='" + self.tenant \
                   + "'}"
