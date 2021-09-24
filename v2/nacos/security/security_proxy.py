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

    def __init__(self, logger, properties: dict):
        self.logger = logger
        self.username = properties[PropertyKeyConstants.USERNAME]
        self.password = properties[PropertyKeyConstants.PASSWORD]
        context_path = properties[PropertyKeyConstants.CONTEXT_PATH].strip()
        self.context_path = context_path if context_path[0] == "/" else "/" + context_path
        self.access_token = ""
        self.token_ttl = 0
        self.token_refresh_window = 0
        self.last_refresh_time = 0

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
        params = {PropertyKeyConstants.USERNAME: self.username,
                  PropertyKeyConstants.PASSWORD: self.password
                  }
        url = UtilAndComs.HTTP + server + self.context_path + SecurityProxy.LOGIN_URL

        if Constants.HTTP_PREFIX in server:
            url = server + self.context_path + SecurityProxy.LOGIN_URL

        try:
            req = Request(url=url, data=urlencode(params).encode('utf-8') if params else None, method="POST")
            resp = urlopen(req)
            resp_data = resp.read()
            message = json.loads(resp_data.decode('utf-8'))
            if resp.getcode() != 0 and resp.getcode() != 200:
                self.logger.error("Login fail: %s" % resp)
                return False
            if Constants.ACCESS_TOKEN in message.keys():
                self.access_token = message.get(Constants.ACCESS_TOKEN)
                self.token_ttl = message.get(Constants.TOKEN_TTL)
                self.token_refresh_window = self.token_ttl/10
        except URLError as e:
            self.logger.error("[SecurityProxy] Login http request failed url: %s, params: %s, errorMsg: %s"
                              % (url, params, e))
            return False
        except NacosException as e:
            self.logger.error("[SecurityProxy] Login http request failed url: %s, params: %s, errorMsg: %s"
                              % (url, params, e))
            return False

        return True

    def get_access_token(self) -> str:
        return self.access_token

    def is_enabled(self) -> bool:
        return self.username.strip() != ""
