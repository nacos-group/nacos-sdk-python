import json
import logging
import sched
import time
from concurrent.futures import ThreadPoolExecutor
from random import randint
from threading import RLock
from typing import List
from urllib.request import Request, urlopen

from v2.nacos.common.lifecycle.closeable import Closeable
from v2.nacos.common.utils import get_current_time_millis
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.property_key_constants import PropertyKeyConstants
from v2.nacos.remote.iserver_list_factory import ServerListFactory


class ServerListManager(ServerListFactory, Closeable):
    def __init__(self, properties: dict):
        logging.basicConfig()
        self.logger = logging.getLogger(__name__)
        self.refresh_server_list_internal = 30  # second
        self.current_index = 0
        self.server_list = []
        self.server_from_endpoint = []
        self.refresh_server_list_executor = None
        self.endpoint = ""
        self.nacos_domain = ""
        self.last_server_list_refresh_time = 0
        self.lock = RLock()

        self.__init_server_addr(properties)
        if self.server_list:
            self.current_index = randint(0, len(self.server_list))

    def __init_server_addr(self, properties: dict) -> None:
        self.endpoint = properties["endpoint"].strip()
        if self.endpoint:
            self.server_from_endpoint = self.__get_server_list_from_endpint()
            self.refresh_server_list_executor = ThreadPoolExecutor(max_workers=1)
            self.timer = sched.scheduler(time.time, time.sleep)
            self.timer.enter(self.refresh_server_list_internal, 0, self.__refresh_server_list_if_need)
            self.refresh_server_list_executor.submit(self.timer.run)
        else:
            server_list_from_props = properties[PropertyKeyConstants.SERVER_ADDR]
            if server_list_from_props:
                self.server_list.extend(server_list_from_props.split(","))
                if len(self.server_list) == 1:
                    self.nacos_domain = server_list_from_props

    def __get_server_list_from_endpint(self) -> list:
        try:
            url_str = "http://" + self.endpoint + "/nacos/serverlist"
            req = Request(url=url_str)
            resp = urlopen(req)
            resp_data = resp.read()
            obj = json.loads(resp_data).decode('utf-8')
            # todo check if wrong
            if obj["code"] != 0 and obj["code"] != 200:
                raise NacosException("Error while requesting")

            content = eval(obj["message"])
            ll = []
            content = content.split()
            for line in content:
                if line.strip():
                    ll.append(line.strip())
            return ll
        except NacosException as e:
            self.logger.error("[Server-LIST] Fail to update server list." + str(e))
        return

    def __refresh_server_list_if_need(self) -> None:
        try:
            if self.server_list:
                self.logger.debug("server list provided by user: " + str(self.server_list))
                return
            if get_current_time_millis() - self.last_server_list_refresh_time < self.refresh_server_list_internal:
                return

            l = self.__get_server_list_from_endpint()

            if not l:
                raise NacosException("Can not acquire Nacos list")

            if not self.server_from_endpoint or l != self.server_from_endpoint:
                self.logger.info("[SERVER-LIST] Server list is updated: " + l)

            self.server_from_endpoint = l
            self.last_server_list_refresh_time = get_current_time_millis()
        except NacosException as e:
            self.logger.warning("Failed to update server list" + e)

    def is_domain(self) -> bool:
        return True if self.nacos_domain else False

    def get_nacos_domain(self) -> str:
        return self.nacos_domain

    def gen_next_server(self) -> str:
        with self.lock:
            self.current_index = (self.current_index + 1) % len(self.get_server_list())
        return self.get_server_list()[self.current_index]

    def get_current_server(self) -> str:
        server_list = self.get_server_list()
        return server_list[self.current_index % len(server_list)]

    def get_server_list(self) -> List[str]:
        return self.server_from_endpoint if not self.server_list else self.server_list

    def shutdown(self) -> None:
        self.logger.info("%s do shutdown begin" % self.__class__.__name__)
        if self.refresh_server_list_executor:
            self.refresh_server_list_executor.shutdown()
        # todo NamingHttpClientManager
        self.logger.info("%s do shutdown stop" % self.__class__.__name__)