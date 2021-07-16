from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class ConfigBatchListenRequest(request.Request):
    def __init__(self):
        super().__init__()
        self.__MODULE = "config"
        self.__listen = True
        self.__config_listen_contexts = []

    def get_module(self):
        return self.__MODULE

    def get_remote_type(self):
        return remote_request_type["ConfigBatchListen"]

    def add_config_listen_context(self, group, data_id, tenant, md5):
        config_listen_context = ConfigBatchListenRequest.ConfigListenContext()
        config_listen_context.group = group
        config_listen_context.data_id = data_id
        config_listen_context.tenant = tenant
        config_listen_context.md5 = md5
        self.__config_listen_contexts.append(config_listen_context)


    class ConfigListenContext:
        def __init__(self):
            self.group = ""
            self.md5 = ""
            self.data_id = ""
            self.tenant = ""

        def __str__(self):
            return "ConfigListenContext{group='" + self.group + "', md5='" + self.md5 + "', data_id='" + self.data_id \
                   + "', tenant='" + self.tenant + "'}"
