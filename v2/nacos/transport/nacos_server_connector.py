import asyncio
from random import randrange
from typing import List, Optional

from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM, INVALID_SERVER_STATUS
from v2.nacos.transport.auth_client import AuthClient
from v2.nacos.transport.http_agent import HttpAgent


class NacosServerConnector:
    def __init__(self, logger, client_config: ClientConfig, http_agent: HttpAgent):
        self.logger = logger

        if len(client_config.server_list) == 0 and not client_config.endpoint:
            raise NacosException(INVALID_PARAM, "both server list and endpoint are empty")

        self.client_config = client_config
        self.server_list = client_config.server_list
        self.current_index = 0
        self.http_agent = http_agent
        self.endpoint = client_config.endpoint
        self.server_list_lock = asyncio.Lock()

        self.refresh_server_list_internal = 30  # second
        if len(self.server_list) != 0:
            self.current_index = randrange(0, len(self.server_list))

        if client_config.username and client_config.password:
            self.auth_client = AuthClient(self.logger, client_config, self.get_server_list, http_agent)
            asyncio.create_task(self.auth_client.get_access_token(True))

    async def init(self):
        if len(self.server_list) != 0:
            return

        await self._get_server_list_from_endpoint()
        if len(self.server_list) == 0:
            raise NacosException(INVALID_SERVER_STATUS, "server list is empty")
        asyncio.create_task(self._refresh_server_srv_if_need())

    async def _get_server_list_from_endpoint(self) -> Optional[List[str]]:
        if not self.endpoint or self.endpoint.strip() == "":
            return None

        url = self.endpoint.strip() + self.client_config.endpoint_context_path + "/serverlist"
        server_list = []
        try:
            response, err = await self.http_agent.request(url, "GET", self.client_config.endpoint_query_header, None,
                                                          None)
            if err:
                self.logger.error("[get-server-list] get server list from endpoint failed,url:%s, err:%s", url, err)
                return None
            else:
                self.logger.debug("[get-server-list] content from endpoint,url:%s,response:%s", url, response)
                if response:
                    for server_info in response.decode('utf-8').strip().split("\n"):
                        sp = server_info.strip().split(":")
                        if len(sp) == 1:
                            server_list.append((sp[0] + ":" + str(Constants.DEFAULT_PORT)))
                        else:
                            server_list.append(server_info)

                    if len(server_list) != 0 and set(server_list) != set(self.server_list):
                        async with self.server_list_lock:
                            old_server_list = self.server_list
                            self.server_list = server_list
                            self.current_index = randrange(0, len(self.server_list))
                            self.logger.info("nacos server list is updated from %s to %s",
                                             str(old_server_list), str(server_list))
        except Exception as e:
            self.logger.error("[get-server-list] get server list from endpoint failed,url:%s, err:%s", url, e)
        return server_list

    async def _refresh_server_srv_if_need(self):
        while True:
            await asyncio.sleep(self.refresh_server_list_internal)

            server_list = await self._get_server_list_from_endpoint()

            if not server_list or len(server_list) == 0:
                self.logger.warning("failed to get server list from endpoint, endpoint: " + self.endpoint)

    def get_server_list(self):
        return self.server_list

    def get_next_server(self):
        if not self.server_list:
            raise NacosException(INVALID_SERVER_STATUS, 'server list is empty')
        self.current_index = (self.current_index + 1) % len(self.server_list)
        return self.server_list[self.current_index]

    async def inject_security_info(self, headers):
        if self.client_config.username and self.client_config.password:
            access_token = await self.auth_client.get_access_token(False)
            if access_token is not None and access_token != "":
                headers[Constants.ACCESS_TOKEN] = access_token
            return
