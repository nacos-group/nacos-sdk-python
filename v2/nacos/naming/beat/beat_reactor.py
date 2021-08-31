import logging
from concurrent.futures import ThreadPoolExecutor

from v2.nacos.common.lifecycle.closeable import Closeable
from v2.nacos.naming.beat.beat_info import BeatInfo
from v2.nacos.naming.dtos.instance import Instance
from v2.nacos.naming.utils.util_and_coms import UtilAndComs


class BeatReactor(Closeable):

    CLIENT_BEAT_INTERVAL_FIELD = "clientBeatInterval"

    def __init__(self, logger, server_proxy=None, properties=None):
        # logging.basicConfig()
        # self.logger = logging.getLogger(__name__)
        self.logger = logger

        self.server_proxy = server_proxy
        self.light_beat_enabled = False
        self.dom2beat = {}

        thread_count = self.__init_client_beat_thread_count(properties)
        self.executor_service = ThreadPoolExecutor(thread_count)
        # todo

    def __init_client_beat_thread_count(self, properties):
        if not properties:
            return UtilAndComs.DEFAULT_POLLING_THREAD_COUNT
        # return ConvertUtils.to_int(properties[])
        # todo

    def add_beat_info(self, service_name: str, beat_info: BeatInfo) -> None:
        pass

    def remove_beat_info(self, service_name: str, ip: str, port: int) -> None:
        pass

    def build_beat_info(self, instance: Instance, grouped_service_name=None) -> BeatInfo:
        pass

    def build_key(self, service_name: str, ip: str, port: int) -> str:
        pass

    def shutdown(self) -> None:
        pass


class BeatTask:
    def __init__(self, beat_info: BeatInfo):
        self.beat_info = beat_info

    def run(self):
        pass