import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from threading import RLock

from v2.nacos.common.lifecycle.closeable import Closeable
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.naming.cache.service_info_holder import ServiceInfoHolder
from v2.nacos.naming.dtos.service_info import ServiceInfo
from v2.nacos.naming.event.instances_change_notifier import InstancesChangeNotifier
from v2.nacos.naming.remote.inaming_client_proxy import NamingClientProxy
from v2.nacos.naming.utils.naming_utils import NamingUtils
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

        self.lock = RLock()

    def schedule_update_if_absent(self, service_name: str, group_name: str, clusters: str) -> None:
        service_key = ServiceInfo.get_key(NamingUtils.get_grouped_name(service_name, group_name), clusters)
        if self.future_map.get(service_key):
            return
        with self.lock:
            if self.future_map.get(service_key):
                return
            future = self.__add_task(self.__update_task(service_name, group_name, clusters))
            self.future_map[service_key] = future

    def stop_update_if_contain(self, service_name: str, group_name: str, clusters: str) -> None:
        service_key = ServiceInfo.get_key(NamingUtils.get_grouped_name(service_name, group_name), clusters)
        if service_key not in self.future_map.keys():
            return
        with self.lock:
            self.future_map.pop(service_key, None)

    def shutdown(self) -> None:
        self.logger.info("%s do shutdown begin" % self.__class__.__name__)
        self.executor.shutdown()
        self.logger.info("%s do shutdown stop" % self.__class__.__name__)

    def __add_task(self, task: threading.Timer):
        return self.executor.submit(task.start)

    def __update_task(self, service_name: str, group_name: str, clusters: str):
        state = ServiceInfoUpdateService.UpdateModel(service_name, group_name, clusters, self)
        return threading.Timer(ServiceInfoUpdateService.DEFAULT_DELAY/1000, state.run)

    class UpdateModel:
        def __init__(self, service_name: str, group_name: str, clusters: str, outer):
            self.service_name = service_name
            self.group_name = group_name
            self.clusters = clusters
            self.grouped_service_name = NamingUtils.get_grouped_name(service_name, group_name)
            self.service_key = ServiceInfo.get_key(self.grouped_service_name, clusters)

            self.last_ref_time = sys.maxsize
            self.fail_count = 0
            self.outer = outer

        def inc_fail_count(self):
            limit = 6
            if self.fail_count == limit:
                return
            self.fail_count += 1

        def reset_fail_count(self):
            self.fail_count = 0

        def run(self):
            delay_time = ServiceInfoUpdateService.DEFAULT_DELAY

            try:
                if not self.outer.change_notifier.is_subscribed(self.group_name, self.service_name, self.clusters) and \
                        self.service_key not in self.outer.future_map.keys():
                    self.outer.logger.info("update task is stopped, service:%s, clusters:%s"
                                     % (self.grouped_service_name, self.clusters))
                    return

                service_obj = self.outer.service_info_holder.get_service_info_map().get(self.service_key)
                if not service_obj:
                    service_obj = self.outer.naming_client_proxy.query_instances_of_service(
                        self.service_name, self.group_name, self.clusters, 0, False)
                    self.outer.service_info_holder.process_service_info(service_obj)
                    self.last_ref_time = service_obj.get_last_ref_time()
                    return

                if service_obj.get_last_ref_time() <= self.last_ref_time:
                    service_obj = self.outer.naming_client_proxy.query_instances_of_service(
                        self.service_name, self.group_name, self.clusters, 0, False
                    )

                self.last_ref_time = service_obj.get_last_ref_time()
                if not service_obj.get_hosts():
                    self.inc_fail_count()
                    return

                delay_time = service_obj.get_cache_millis() * ServiceInfoUpdateService.DEFAULT_UPDATE_CACHE_TIME_MULTIPLE
                self.reset_fail_count()
            except NacosException as e:
                self.inc_fail_count()
                self.outer.logger.warning("[NA] failed to update serviceName: %s" % str(e))
            finally:
                due = min(delay_time << self.fail_count, ServiceInfoUpdateService.DEFAULT_DELAY * 60)
                t = threading.Timer(due/1000, self.run)
                # self.outer.executor.submit(t.start)
