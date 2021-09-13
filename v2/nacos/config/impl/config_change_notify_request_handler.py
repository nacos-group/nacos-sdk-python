from threading import RLock

from v2.nacos.common.utils import get_current_time_millis
from v2.nacos.config.common.group_key import GroupKey
from v2.nacos.remote.requests import ConfigChangeNotifyRequest
from v2.nacos.remote.requests.request import Request
from v2.nacos.remote.responses import ConfigChangeNotifyResponse
from v2.nacos.remote.responses.response import Response


class ConfigRpcServerRequestHandler:
    def __init__(self, cache_map: dict, func):
        self.cache_map = cache_map
        self.func = func
        self.lock = RLock()

    def request_reply(self, request: Request) -> Response:
        if isinstance(request, ConfigChangeNotifyRequest):
            group_key = GroupKey.get_key_tenant(request.dataId, request.group, request.tenant)

            if group_key in self.cache_map.keys():
                cache_data = self.cache_map[group_key]
                if cache_data:
                    with self.lock:
                        cache_data.set_last_modified_ts(get_current_time_millis())
                        cache_data.set_sync_with_server(False)
                        self.func()
            return ConfigChangeNotifyResponse()
        return
