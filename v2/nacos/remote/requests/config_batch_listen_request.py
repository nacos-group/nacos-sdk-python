from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class ConfigBatchListenRequest(request.Request):
    configListenContexts: list = []
    listen: bool = True

    def get_module(self):
        return "config"

    def get_remote_type(self):
        return remote_request_type["ConfigBatchListen"]

    def add_config_listen_context(self, group: str, data_id: str, tenant: str, md5: str) -> None:
        config_listen_context = ConfigBatchListenRequest.ConfigListenContext(group, data_id, tenant, md5)
        self.configListenContexts.append(config_listen_context)

    class ConfigListenContext:
        def __init__(self, group: str, data_id: str, tenant: str, md5: str):
            self.group = group
            self.dataId = data_id
            self.tenant = tenant
            self.md5 = md5

        def __str__(self):
            return "ConfigListenContext{group='" + self.group + "', md5='" + self.md5 + "', dataId='" + self.dataId \
                   + "', tenant='" + self.tenant + "'}"
