from v2.nacos.naming.cache.service_info_holder import ServiceInfoHolder
from v2.nacos.remote.iserver_request_handler import ServerRequestHandler
from v2.nacos.remote.requests.notify_subscriber_request import NotifySubscriberRequest
from v2.nacos.remote.requests.request import Request
from v2.nacos.remote.responses.notify_subscriber_response import NotifySubscriberResponse
from v2.nacos.remote.responses.response import Response


class NamingPushRequestHandler(ServerRequestHandler):
    def __init__(self, service_info_holder: ServiceInfoHolder):
        self.service_info_holder = service_info_holder

    def request_reply(self, request: Request) -> Response:
        if isinstance(request, NotifySubscriberRequest):
            self.service_info_holder.process_service_info(request.get_service_info())
            response = NotifySubscriberResponse()
            response.set_request_id(request.get_request_id())
            return response
        return
