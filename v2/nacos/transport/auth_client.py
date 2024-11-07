import json
import time

from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.nacos_exception import NacosException, SERVER_ERROR
from v2.nacos.transport.http_agent import HttpAgent


class AuthClient:
    def __init__(self, logger, client_config: ClientConfig, get_server_list_func, http_agent: HttpAgent):
        self.logger = logger
        self.username = client_config.username
        self.password = client_config.password
        self.client_config = client_config
        self.get_server_list = get_server_list_func
        self.http_agent = http_agent
        self.access_token = None
        self.token_ttl = 0
        self.last_refresh_time = 0
        self.token_expired_time = None

    async def get_access_token(self, force_refresh=False):
        current_time = time.time()
        if self.access_token and not force_refresh and self.token_expired_time > current_time:
            return self.access_token

        params = {
            "username": self.username,
            "password": self.password
        }

        server_list = self.get_server_list()
        for server_address in server_list:
            url = server_address + "/nacos/v1/auth/users/login"
            resp, error = await self.http_agent.request(url, "POST", None, params, None)
            if not resp or error:
                self.logger.warning(f"[get-access-token] request {url} failed, error: {error}")
                continue

            response_data = json.loads(resp.decode("UTF-8"))
            self.access_token = response_data.get('accessToken')
            self.token_ttl = response_data.get('tokenTtl', 18000)  # 默认使用返回值，无返回则使用18000秒
            self.token_expired_time = current_time + self.token_ttl - 10  # 更新 Token 的过期时间
            self.logger.info(
                f"[get_access_token] AccessToken: {self.access_token}, TTL: {self.token_ttl}, force_refresh: {force_refresh}")
            return self.access_token
        raise NacosException(SERVER_ERROR, "get access token failed")
