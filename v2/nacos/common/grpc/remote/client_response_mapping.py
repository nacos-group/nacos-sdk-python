import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict
from ....util import commom


# 响应映射字典
class ClientResponseMapping:  #从rpc_respnse中抽取出来的ClientResponseMapping，这个有点像kms的manager，我要看下Java怎么实现的
    _mapping = {}

    @classmethod
    def register_client_response(cls, response):
        response_type = response().get_response_type()
        if not response_type:
            print("Register client response error: response_type is nil")
            return
        cls._mapping[response_type] = response

    @classmethod
    def get_response(cls, response_type):
        return cls._mapping.get(response_type, None)()


def register_client_responses():
    ClientResponseMapping.register_client_response(lambda: InstanceResponse())
    ClientResponseMapping.register_client_response(lambda: BatchInstanceResponse())
    ClientResponseMapping.register_client_response(lambda: QueryServiceResponse())
    ClientResponseMapping.register_client_response(lambda: SubscribeServiceResponse())
    ClientResponseMapping.register_client_response(lambda: ServiceListResponse())
    ClientResponseMapping.register_client_response(lambda: NotifySubscriberResponse())
    ClientResponseMapping.register_client_response(lambda: HealthCheckResponse())
    ClientResponseMapping.register_client_response(lambda: ErrorResponse())
    ClientResponseMapping.register_client_response(lambda: ConfigChangeBatchListenResponse())
    ClientResponseMapping.register_client_response(lambda: ConfigQueryResponse())
    ClientResponseMapping.register_client_response(lambda: ConfigPublishResponse())
    ClientResponseMapping.register_client_response(lambda: ConfigRemoveResponse())