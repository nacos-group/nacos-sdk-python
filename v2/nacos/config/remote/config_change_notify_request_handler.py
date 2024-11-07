from v2.nacos.common.constants import Constants
from v2.nacos.config.model.config_request import ConfigChangeNotifyRequest
from v2.nacos.transport.model.internal_response import NotifySubscriberResponse
from v2.nacos.transport.model.rpc_request import Request
from v2.nacos.transport.server_request_handler import IServerRequestHandler
from v2.nacos.utils import common_util


class ConfigChangeNotifyRequestHandler(IServerRequestHandler):
    def __init__(self, client):
        self.client = client

    def name(self):
        return "ConfigChangeNotifyRequestHandler"

    async def request_reply(self, request: Request):
        if not isinstance(request, ConfigChangeNotifyRequest):
            return None

        cache_key = common_util.get_config_cache_key(request.dataId, request.group, request.tenant)
        data = self.client.cache_map.get(cache_key)

        if data is None:
            return None

        c_data = data
        c_data.is_sync_with_server = False
        self.client.cache_map[cache_key] = c_data
        self.client.async_notify_listen_config()

        return NotifySubscriberResponse()
