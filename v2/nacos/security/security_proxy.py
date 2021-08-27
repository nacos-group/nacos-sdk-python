import json
import logging
import urllib
from typing import List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from v2.nacos.common.constants import Constants
from v2.nacos.common.utils import get_current_time_millis
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.naming.utils.util_and_coms import UtilAndComs
from v2.nacos.property_key_constants import PropertyKeyConstants


class SecurityProxy:
    LOGIN_URL = "/v1/auth/users/login"

    def __init__(self, properties: dict):
        logging.basicConfig()
        self.logger = logging.getLogger(__name__)
        self.username = properties[PropertyKeyConstants.USERNAME]
        self.password = properties[PropertyKeyConstants.PASSWORD]
        context_path = properties[PropertyKeyConstants.CONTEXT_PATH].strip()
        self.context_path = context_path if context_path[0] == "/" else "/" + context_path
        self.access_token = ""
        self.token_ttl = None
        self.token_refresh_window = None
        self.last_refresh_time = None

    def login_servers(self, servers: List[str]) -> bool:
        try:
            if get_current_time_millis() - self.last_refresh_time < self.token_ttl - self.token_refresh_window:
                return True

            for server in servers:
                if self.login_server(server):
                    self.last_refresh_time = get_current_time_millis()
                    return True

        except NacosException as e:
            self.logger.warning("[SecurityProxy] login failed, error: " + e)

        return False

    def login_server(self, server: str) -> bool:
        params = {PropertyKeyConstants.USERNAME: self.username}
        body_map = {PropertyKeyConstants.PASSWORD: self.password}
        url = UtilAndComs.HTTP + server + self.context_path + SecurityProxy.LOGIN_URL

        if Constants.HTTP_PREFIX in server:
            url = server + self.context_path + SecurityProxy.LOGIN_URL

        try:
            req = Request(url=url, data=urlencode(params).encode('utf-8') if params else None, method="POST")
            resp = urlopen(req)
            resp_data = resp.read()
            # todo ?
            obj = json.loads(resp_data).decode('utf-8')
            if obj["code"] != 0 and obj["code"] != 200:
                self.logger.error("Login fail: %s" % json.dumps(resp))
                return False
            message = eval(obj["message"])
            if Constants.ACCESS_TOKEN in message.keys():
                self.access_token = str(obj[message.ACCESS_TOKEN])
                self.token_ttl = int(obj[message.TOKEN_TTL])
                self.token_refresh_window = self.token_ttl/10
        except URLError as e:
            self.logger.error("[SecurityProxy] Login http request failed url: %s, params: %s, bodyMap: %s, errorMsg: %s"
                              % (url, params, body_map, e))
            return False
        except NacosException as e:
            self.logger.error("[SecurityProxy] Login http request failed url: %s, params: %s, bodyMap: %s, errorMsg: %s"
                              % (url, params, body_map, e))
            return False

        return True

    def get_access_token(self) -> str:
        return self.access_token

    def is_enabled(self) -> bool:
        return self.username.strip() != ""
