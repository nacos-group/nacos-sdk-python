from typing import Optional

from v2.nacos.naming.cache.service_info_cache import ServiceInfoCache
from v2.nacos.naming.model.naming_request import NotifySubscriberRequest
from v2.nacos.naming.model.naming_response import NotifySubscriberResponse
from v2.nacos.transport.model.rpc_request import Request
from v2.nacos.transport.model.rpc_response import Response
from v2.nacos.transport.server_request_handler import IServerRequestHandler


class NamingPushRequestHandler(IServerRequestHandler):

    def name(self) -> str:
        return "NamingPushRequestHandler"

    def __init__(self, service_info_cache: ServiceInfoCache):
        self.service_info_cache = service_info_cache

    def request_reply(self, request: Request) -> Optional[Response]:
        if isinstance(request, NotifySubscriberRequest):
            self.service_info_cache.process_service(request.get_service_info())
            response = NotifySubscriberResponse()
            return response
        return None
