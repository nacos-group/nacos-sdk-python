import logging
from concurrent.futures import ThreadPoolExecutor

from v2.nacos.common.lifecycle.closeable import Closeable
from v2.nacos.naming.cache.service_info_holder import ServiceInfoHolder
from v2.nacos.naming.event.instances_change_notifier import InstancesChangeNotifier
from v2.nacos.naming.remote.inaming_client_proxy import NamingClientProxy
from v2.nacos.naming.utils.util_and_coms import UtilAndComs


class ServiceInfoUpdateService(Closeable):
    DEFAULT_DELAY = 1000

    DEFAULT_UPDATE_CACHE_TIME_MULTIPLE = 6

    def __init__(self, logger, properties: dict, service_info_holder: ServiceInfoHolder,
                 naming_client_proxy: NamingClientProxy, change_notifier: InstancesChangeNotifier):
        self.logger = logger

        self.future_map = {}

        self.executor = ThreadPoolExecutor(max_workers=UtilAndComs.DEFAULT_POLLING_THREAD_COUNT)

        self.service_info_holder = service_info_holder
        self.naming_client_proxy = naming_client_proxy
        self.change_notifier = change_notifier

    def schedule_update_if_absent(self, service_name: str, group_name: str, clusters: str) -> None:
        pass

    def stop_update_if_contain(self, service_name: str, group_name: str, clusters: str) -> None:
        pass

    def shutdown(self) -> None:
        self.logger.info("%s do shutdown begin" % self.__class__.__name__)
        self.executor.shutdown()
        self.logger.info("%s do shutdown stop" % self.__class__.__name__)
