import json
from datetime import datetime
from typing import List
from .rpc_response import Response
from ..model.config import ConfigContext

class ConfigChangeBatchListenResponse(Response):
    def __init__(self):
        super().__init__()  
        self.changed_configs = [] #这边要用ConfigContext约束

    @staticmethod
    def new_config_change_batch_listen_response():
        return ConfigChangeBatchListenResponse()

    def get_response_type(self) -> str:
        return "ConfigChangeBatchListenResponse"

class ConfigQueryResponse(Response):
    def __init__(self):
        super().__init__()  # 调用父类Response的构造方法
        self.content = ""
        self.encrypted_data_key = ""
        self.content_type = ""
        self.md5 = ""
        self.last_modified = 0  # 假设为Unix时间戳
        self.is_beta = False
        self.tag = False

    @staticmethod
    def new_config_query_response():
        return ConfigQueryResponse()

    def get_response_type(self) -> str:
        return "ConfigQueryResponse"

class ConfigPublishResponse(Response):
    def __init__(self):
        super().__init__()  # 调用父类Response的构造方法

    @staticmethod
    def new_config_publish_response():
        return ConfigPublishResponse()

    def get_response_type(self) -> str:
        return "ConfigPublishResponse"

class ConfigRemoveResponse:
    def __init__(self):
        super().__init__()

    @staticmethod
    def new_config_remove_response():
        return ConfigRemoveResponse()

    def get_response_type(self) -> str:
        return "ConfigRemoveResponse"