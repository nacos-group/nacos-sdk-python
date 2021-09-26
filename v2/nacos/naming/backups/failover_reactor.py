import json
import os
import sched
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

from v2.nacos.common.lifecycle.closeable import Closeable
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.naming.cache.disk_cache import DiskCache
from v2.nacos.naming.dtos.service_info import ServiceInfo
from v2.nacos.naming.utils.util_and_coms import UtilAndComs


class FailoverReactor(Closeable):
    FAILOVER_DIR = "/failover"

    IS_FAILOVER_MODE = "1"

    NO_FAILOVER_MODE = "0"

    FAILOVER_MODE_PARAM = "failover-mode"

    DAY_PERIOD_SECONDS = 24 * 60 * 60
    # DAY_PERIOD_SECONDS = 10 # debug

    def __init__(self, logger, service_info_holder, cache_dir):
        self.logger = logger
        self.service_map = {}
        self.switch_params = {}
        self.service_info_holder = service_info_holder
        self.failover_dir = cache_dir + FailoverReactor.FAILOVER_DIR

        self.executor_service = ThreadPoolExecutor(max_workers=1)

        self.last_modified_time = 0

        self.task_timer = sched.scheduler(time.time, time.sleep)

        self.disk_cache = DiskCache(self.logger)

        self.__init_failover_reactor()

    def __init_failover_reactor(self):
        self.task_timer.enter(5, 0, self.__switch_refresher)
        self.task_timer.enter(FailoverReactor.DAY_PERIOD_SECONDS, 0, self.__disk_file_writer)
        self.executor_service.submit(self.task_timer.run)
        self.executor_service.submit(self.__backup_file)

    def is_failover_switch(self):
        return self.switch_params.get(FailoverReactor.FAILOVER_MODE_PARAM)

    def get_service(self, key: str) -> ServiceInfo:
        service_info = self.service_map.get(key)
        if not service_info:
            service_info = ServiceInfo()
            service_info.set_name(key)
        return service_info

    def shutdown(self) -> None:
        self.logger.info("%s do shutdown begin" % self.__class__.__name__)
        self.executor_service.shutdown(wait=False)
        self.logger.info("%s do shutdown stop" % self.__class__.__name__)

    def __backup_file(self):
        time.sleep(10)
        try:
            if not os.path.exists(self.failover_dir):
                try:
                    os.makedirs(self.failover_dir)
                except OSError:
                    raise OSError("failed to create cache dir: " + self.failover_dir)
            files = os.listdir()
            if not files:
                self.__disk_file_writer()
        except NacosException as e:
            self.logger.error("[NA] failed to backup file on startup, errorMsg: " + str(e))

    def __switch_refresher(self):
        try:
            switch_file = self.failover_dir + UtilAndComs.FAILOVER_SWITCH
            if not os.path.exists(switch_file):
                self.switch_params[FailoverReactor.FAILOVER_MODE_PARAM] = False
                self.logger.debug("failover switch is not found, %s" % switch_file)
                return

            modified = os.stat(switch_file).st_mtime

            if self.last_modified_time < modified:
                self.last_modified_time = modified
                with open(switch_file, "r", encoding='utf-8') as f:
                    failover = f.read()
                if failover:
                    lines = failover.split(DiskCache.get_line_separator())
                    for line in lines:
                        line1 = line.strip()
                        if FailoverReactor.IS_FAILOVER_MODE == line1:
                            self.switch_params[FailoverReactor.FAILOVER_MODE_PARAM] = True
                            self.logger.info("failover-mode is on")
                            self.__failover_file_reader()
                        elif FailoverReactor.NO_FAILOVER_MODE == line1:
                            self.switch_params[FailoverReactor.FAILOVER_MODE_PARAM] = False
                            self.logger.info("failover-mode is off")
                else:
                    self.switch_params[FailoverReactor.FAILOVER_MODE_PARAM] = False
        except NacosException as e:
            self.logger.error("[NA] failed to read failover switch. errorMsg: " + str(e))

    def __failover_file_reader(self):
        dom_map = {}
        try:
            if not os.path.exists(self.failover_dir):
                try:
                    os.makedirs(self.failover_dir)
                except OSError:
                    raise OSError("failed to create cache dir: " + self.failover_dir)

            files = os.listdir()
            if not files:
                return

            for file in files:
                if not os.path.isfile(file):
                    continue

                if os.path.basename(file) == UtilAndComs.FAILOVER_SWITCH:
                    continue

                dom = ServiceInfo()
                dom.init_from_key(os.path.basename(file))

                with open(os.path.join(self.failover_dir, file), "r", encoding="utf-8") as f:
                    json_strs = f.readlines()

                for json_str in json_strs:
                    if json_str.strip():
                        try:
                            json_dict = json.loads(json_str.strip())
                            dom = ServiceInfo.build(json_dict)

                        except NacosException as e:
                            self.logger.error("[NA] error while parsing cached dom: %s, errorMsg: %s"
                                              % (json_str, str(e)))

                if dom.get_hosts():
                    dom_map[dom.get_key_default()] = dom

        except NacosException as e:
            self.logger.error("[NA] failed to read cache file, errorMsg: " + str(e))

        if len(dom_map) > 0:
            self.service_map = dom_map

    def __disk_file_writer(self):
        def timer_task():
            service_info_map = self.service_info_holder.get_service_info_map()

            for key, service_info in service_info_map.items():
                if service_info.get_key() == UtilAndComs.ALL_IPS or \
                        service_info.get_name() == UtilAndComs.ENV_LIST_KEY or \
                        service_info.get_name() == UtilAndComs.ENV_CONFIGS or \
                        service_info.get_name() == UtilAndComs.VIP_CLIENT_FILE or \
                        service_info.get_name() == UtilAndComs.ALL_HOSTS:
                    continue
                self.disk_cache.write(service_info, self.failover_dir)

        return threading.Timer(30*60, timer_task).start()
