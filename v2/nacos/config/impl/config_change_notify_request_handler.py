from threading import RLock
from typing import Optional

from v2.nacos.common.utils import get_current_time_millis
from v2.nacos.config.common.group_key import GroupKey
from v2.nacos.remote.iserver_request_handler import ServerRequestHandler
from v2.nacos.remote.requests.config_change_notify_request import ConfigChangeNotifyRequest
from v2.nacos.remote.requests.request import Request
from v2.nacos.remote.responses import ConfigChangeNotifyResponse
from v2.nacos.remote.responses.response import Response


class ConfigChangeNotifyRequestHandler(ServerRequestHandler):
    def __init__(self, logger, cache_map: dict, func):
        self.logger = logger
        self.cache_map = cache_map
        self.func = func
        self.lock = RLock()

    def request_reply(self, request: Request) -> Optional[Response]:
        if isinstance(request, ConfigChangeNotifyRequest):
            print("ConfigChangeNotifyRequest!")
            self.logger.info("[server-push] config changed. dataId=%s, group=%s, tenant=%s"
                             % (request.get_data_id(), request.get_group(), request.get_tenant()))
            group_key = GroupKey.get_key_tenant(request.dataId, request.group, request.tenant)

            cache_data = self.cache_map.get(group_key)
            if cache_data:
                with self.lock:
                    cache_data.set_last_modified_ts(get_current_time_millis())
                    cache_data.set_sync_with_server(False)
                    self.func()

            return ConfigChangeNotifyResponse()
        return
