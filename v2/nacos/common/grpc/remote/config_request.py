from .rpc_request import Request, IConfigRequest
from ..model.config import ConfigListenContext 
class ConfigRequest(Request):
    def __init__(self, group, data_id, tenant):
        super().__init__()
        self.Group = group
        self.DataId = data_id
        self.Tenant = tenant
        self.Module = "config"

    @staticmethod
    def new_config_request(group, data_id, tenant):
        return ConfigRequest(group, data_id, tenant)

    def GetDataId(self):
        return self.DataId

    def GetGroup(self):
        return self.Group

    def GetTenant(self):
        return self.Tenant

class ConfigBatchListenRequest(ConfigRequest):
    def __init__(self, cache_len):
        super().__init__("", "", "")  # 调用父类ConfigRequest的构造方法
        self.listen = True
        self.config_listen_contexts = [ConfigListenContext() for _ in range(cache_len)]  # 创建指定长度的列表

    @staticmethod
    def new_config_batch_listen_request(cache_len):
        return ConfigBatchListenRequest(cache_len)

    def GetRequestType(self):
        return "ConfigBatchListenRequest"

class ConfigChangeNotifyRequest(ConfigRequest):
    def __init__(self, group, data_id, tenant):
        super().__init__(group, data_id, tenant)  # 调用父类的构造方法

    @staticmethod
    def new_config_change_notify_request(group, data_id, tenant):
        return ConfigChangeNotifyRequest(group, data_id, tenant)

    def get_request_type(self):
        return "ConfigChangeNotifyRequest"

class ConfigQueryRequest(ConfigRequest):
    def __init__(self, group, data_id, tenant, tag):
        super().__init__(group, data_id, tenant)
        self.tag = tag

    @staticmethod
    def new_config_query_request(group, data_id, tenant, tag):
        return ConfigQueryRequest(group, data_id, tenant, tag)

    def get_request_type(self):
        return "ConfigQueryRequest"

class ConfigPublishRequest(ConfigRequest):
    def __init__(self, group, data_id, tenant, content, cas_md5, addition_map=None):
        super().__init__(group, data_id, tenant)
        self.content = content
        self.cas_md5 = cas_md5
        self.addition_map = addition_map if addition_map is not None else {}

    @staticmethod
    def new_config_publish_request(group, data_id, tenant, content, cas_md5):
        return ConfigPublishRequest(group, data_id, tenant, content, cas_md5)

    def get_request_type(self):
        return "ConfigPublishRequest"

class ConfigRemoveRequest(ConfigRequest):
    def __init__(self, group, data_id, tenant):
        super().__init__(group, data_id, tenant)

    @staticmethod
    def new_config_remove_request(group, data_id, tenant):
        return ConfigRemoveRequest(group, data_id, tenant)

    def get_request_type(self):
        return "ConfigRemoveRequest"