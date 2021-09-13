import re
import sched
import time
from concurrent.futures import ThreadPoolExecutor
from threading import RLock
from urllib.request import Request, urlopen
from v2.nacos.common.lifecycle.closeable import Closeable
from v2.nacos.common.internet_address_util import InternetAddressUtil
from v2.nacos.common.utils import synchronized_with_attr
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.property_key_constants import PropertyKeyConstants


class ServerListManager(Closeable):
    HTTPS = "https://"

    HTTP = "http://"

    DEFAULT_NAME = "default"

    CUSTOM_NAME = "custom"

    FIXED_NAME = "fixed"

    TIMEOUT = 5000

    def __init__(self, logger, properties: dict):
        self.logger = logger
        self.name = None
        namespace = properties.get(PropertyKeyConstants.NAMESPACE)
        self.namespace = None
        self.tenant = None
        self.init_server_list_retry_times = 5
        self.fixed = False
        self.started = False
        self.endpoint = properties.get(PropertyKeyConstants.ENDPOINT)
        self.endpoint_port = 8000
        self.content_path = properties.get(PropertyKeyConstants.CONTEXT_PATH)  # use the input of user
        self.server_list_name = "serverlist"
        self.server_urls = []
        self.current_server_addr = None
        self.address_server_url = None
        self.server_addrs_str = properties.get(PropertyKeyConstants.SERVER_ADDR)

        self.lock = RLock()
        self.timer = sched.scheduler(time.time, time.sleep)
        self.executor_service = ThreadPoolExecutor(max_workers=1)

        if self.server_addrs_str and self.server_addrs_str.strip():
            self.fixed = True
            server_addrs_tokens = self.server_addrs_str.spilt(",;")
            for token in server_addrs_tokens:
                # trust the input server addresses of user
                self.server_urls.append(token.strip())
            if not namespace:
                self.name = ServerListManager.FIXED_NAME + "-" + self.__get_fixed_name_suffix(self.server_urls)
            else:
                self.namespace = namespace
                self.tenant = namespace
                self.name = ServerListManager.FIXED_NAME + "-" + self.__get_fixed_name_suffix(
                    self.server_urls) + "-" + namespace
        else:
            if not self.endpoint:
                raise NacosException("endpoint is blank")
            self.fixed = False
            if not namespace:
                self.namespace = self.endpoint_port
                self.tenant = namespace
                self.name = self.endpoint + "-" + namespace
                self.address_server_url = "http://" + self.endpoint + ":" + \
                                          str(self.endpoint_port) + self.content_path + "/" + self.server_list_name
            else:
                self.namespace = namespace
                self.tenant = namespace
                self.name = self.endpoint + "-" + namespace
                self.address_server_url = "http://" + self.endpoint + ":" + \
                                          str(self.endpoint_port) + self.content_path + "/" + self.server_list_name + \
                                          "?namespace=" + namespace

    @staticmethod
    def __get_fixed_name_suffix(server_ips: list) -> str:
        sb = ""
        spilt = ""
        for server_ip in server_ips:
            sb += spilt
            server_ip = re.sub(r"http(s)?://", "", server_ip)
            server_ip = re.sub(r":", "", server_ip)
            sb += server_ip
            spilt = "-"
        return sb

    @synchronized_with_attr("lock")
    def start(self) -> None:
        if self.started or self.fixed:
            return

        get_servers_task = ...

        i = 0
        while i < self.init_server_list_retry_times and not self.server_urls:
            try:
                get_servers_task.run()
                pass
            except NacosException:
                self.logger.warning("get serverlist fail, url: %s" % self.address_server_url)
            i += 1

        if not self.server_urls:
            self.logger.error("[init-serverlist] fail to get nacos-server serverlist! env: %s, url: %s"
                              % (self.name, self.address_server_url))
            raise NacosException(
                str(NacosException.SERVER_ERROR) + "fail to get nacos-server serverlist! env: " + self.name
                + ", not connect url: " + self.address_server_url
            )

        self.timer.enter(0.03, 0, get_servers_task.run, ())
        self.executor_service.submit(self.timer.run)
        self.started = True

    def get_server_urls(self) -> list:
        return self.server_urls

    def shutdown(self) -> None:
        pass

    def update_if_changed(self, new_list: list) -> None:
        if not new_list:
            self.logger.warning("[update-serverlist] current serverlist from address server is empty!!!")
            return

        new_server_addr_list = []
        for server in new_list:
            if server.startswith(ServerListManager.HTTP) or server.startswith(ServerListManager.HTTPS):
                new_server_addr_list.append(server)
            else:
                new_server_addr_list.append(ServerListManager.HTTP + server)

        # if there is no change
        if set(new_server_addr_list) == set(self.server_urls):
            return

        self.server_urls = new_server_addr_list
        self.current_server_addr = self.server_urls[0]

        self.logger.info("[%s] [update-serverlist] serverlist update to %s"
                         % (self.name, str(self.server_urls)))

    class GetServerListTask:
        def __init__(self, logger, name, url, func):
            self.logger = logger
            self.name = name
            self.url = url
            self.func = func

        def run(self):
            try:
                self.func(self.__get_apache_server_list())
            except NacosException as e:
                self.logger.error(
                    "[" + self.url + "] [update-serverlist] failed to update serverlist from address server!" + str(e)
                )

        def __get_apache_server_list(self):
            req = Request(url=self.url, method="GET")
            resp = urlopen(req)
            if resp.getcode() == 0 or resp.getcode() == 200:
                pass


