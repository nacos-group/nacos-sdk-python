from abc import ABC
from typing import Optional, Any, List

from v2.nacos.naming.model.instance import Instance
from v2.nacos.naming.model.service import Service
from v2.nacos.transport.model.rpc_request import Request


class AbstractNamingRequest(Request, ABC):
    namespace: Optional[str] = ''
    serviceName: Optional[str] = ''
    groupName: Optional[str] = ''

    def get_module(self):
        return "naming"

    def get_request_type(self) -> str:
        """
        提供一个默认实现或抛出NotImplementedError，明确指示子类需要覆盖此方法。
        """
        raise NotImplementedError("Subclasses should implement this method.")


NOTIFY_SUBSCRIBER_REQUEST_TYPE = "NotifySubscriberRequest"

class ServiceQueryRequest(AbstractNamingRequest):
    cluster: Optional[str]
    healthOnly: Optional[bool]
    udpPort: Optional[int] = None

    def get_request_type(self) -> str:
        return 'ServiceQueryRequest'


class InstanceRequest(AbstractNamingRequest):
    type: Optional[str]
    instance: Optional[Instance]

    def get_request_type(self) -> str:
        return 'InstanceRequest'

class PersistentInstanceRequest(AbstractNamingRequest):
    type: Optional[str]
    instance: Optional[Instance]
    def get_request_type(self) -> str:
        return 'PersistentInstanceRequest'


class BatchInstanceRequest(AbstractNamingRequest):
    type: Optional[str]
    instances: Optional[List[Instance]]

    def get_request_type(self) -> str:
        return 'BatchInstanceRequest'


class NotifySubscriberRequest(AbstractNamingRequest):
    serviceInfo: Optional[Service]

    def get_request_type(self) -> str:
        return 'NotifySubscriberRequest'


class ServiceListRequest(AbstractNamingRequest):
    pageNo: Optional[int]
    pageSize: Optional[int]

    def get_request_type(self) -> str:
        return 'ServiceListRequest'


class SubscribeServiceRequest(AbstractNamingRequest):
    subscribe: Optional[bool]
    clusters: Optional[str]

    def get_request_type(self) -> str:
        return 'SubscribeServiceRequest'
