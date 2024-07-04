# -*- coding=utf-8 -*-
import base64
import functools
import hashlib
import hmac
import json
import logging
import os
import platform
import socket
import threading
import time
from logging.handlers import TimedRotatingFileHandler
from typing import Dict

from .task import HeartbeatInfo, HeartbeatTask

try:
    import ssl
except ImportError:
    ssl = None

from multiprocessing import Process, Manager, Queue, pool
from threading import RLock, Thread

try:
    # python3.6
    from http import HTTPStatus
    from urllib.request import Request, urlopen, ProxyHandler, HTTPSHandler, build_opener
    from urllib.parse import urlencode, unquote_plus, quote
    from urllib.error import HTTPError, URLError
except ImportError:
    # python2.7
    import httplib as HTTPStatus
    from urllib2 import Request, urlopen, HTTPError, URLError, ProxyHandler, HTTPSHandler, build_opener
    from urllib import urlencode, unquote_plus, quote

    base64.encodebytes = base64.encodestring

from .commons import synchronized_with_attr, truncate, python_version_bellow
from .params import group_key, parse_key, is_valid
from .files import read_file_str, save_file, delete_file
from .exception import NacosException, NacosRequestException
from .listener import Event, SimpleListenerManager
from .timer import NacosTimer, NacosTimerManager

logger = logging.getLogger(__name__)

VERSION = "0.1.16"

DEFAULT_GROUP_NAME = "DEFAULT_GROUP"
DEFAULT_NAMESPACE = ""
ADDRESS_SERVER_TIMEOUT = 3
WORD_SEPARATOR = u'\x02'
LINE_SEPARATOR = u'\x01'

DEFAULTS = {
    "APP_NAME": "Nacos-SDK-Python",
    "TIMEOUT": 3,  # in seconds
    "PULLING_TIMEOUT": 30,  # in seconds
    "PULLING_CONFIG_SIZE": 3000,
    "CALLBACK_THREAD_NUM": 10,
    "FAILOVER_BASE": "nacos-data/data",
    "SNAPSHOT_BASE": "nacos-data/snapshot",
}

OPTIONS = {"default_timeout", "pulling_timeout", "pulling_config_size", "callback_thread_num", "failover_base",
           "snapshot_base", "no_snapshot", "proxies"}


def process_common_config_params(data_id, group):
    if not group or not group.strip():
        group = DEFAULT_GROUP_NAME
    else:
        group = group.strip()

    if not data_id or not is_valid(data_id):
        raise NacosException("Invalid dataId.")

    if not is_valid(group):
        raise NacosException("Invalid group.")
    return data_id, group


def parse_pulling_result(result):
    if not result:
        return list()
    ret = list()
    for i in unquote_plus(result.decode()).split(LINE_SEPARATOR):
        if not i.strip():
            continue
        sp = i.split(WORD_SEPARATOR)
        if len(sp) < 3:
            sp.append("")
        ret.append(sp)
    return ret


class WatcherWrap:
    def __init__(self, key, callback, last_md5=None):
        self.callback = callback
        self.last_md5 = last_md5
        self.watch_key = key


class CacheData:
    def __init__(self, key, client):
        self.key = key
        local_value = read_file_str(client.failover_base, key) or read_file_str(client.snapshot_base, key)
        self.content = local_value
        self.md5 = hashlib.md5(local_value.encode("UTF-8")).hexdigest() if local_value else None
        self.is_init = True
        if not self.md5:
            logger.info("[init-cache] cache for %s does not have local value" % key)


class SubscribedLocalInstance(object):
    def __init__(self, key, instance):
        self.key = key
        self.instance_id = instance["instanceId"]
        self.md5 = NacosClient.get_md5(str(instance))
        self.instance = instance


class SubscribedLocalManager(object):
    def __init__(self):
        self.manager = {
            # "key1": {
            #     "LOCAL_INSTANCES": {
            #         "instanceId1": None,
            #         "instanceId2": None,
            #         "instanceId3": None,
            #         "instanceId4": None
            #     },
            #     "LISTENER_MANAGER": None
            # },
            # "key2": {
            #     "LOCAL_INSTANCES": {
            #         "instanceId1": "",
            #         "instanceId2": "",
            #         "instanceId3": "",
            #         "instanceId4": ""
            #     },
            #     "LISTENER_MANAGER": None
            # }
        }

    def do_listener_launch(self, key, event, slc):
        listener_manager = self.get_local_listener_manager(key)
        if listener_manager and isinstance(listener_manager, SimpleListenerManager):
            listener_manager.do_launch(event, slc)

    def get_local_listener_manager(self, key):
        key_node = self.manager.get(key)
        if not key_node:
            return None
        return key_node.get("LISTENER_MANAGER")

    def add_local_listener(self, key, listener_fn):
        if not self.manager.get(key):
            self.manager[key] = {}
        local_listener_manager = self.manager.get(key).get("LISTENER_MANAGER")

        if not local_listener_manager or not isinstance(local_listener_manager, SimpleListenerManager):
            self.manager.get(key)["LISTENER_MANAGER"] = SimpleListenerManager()
        local_listener_manager = self.manager.get(key).get("LISTENER_MANAGER")
        if not local_listener_manager:
            return self
        if isinstance(listener_fn, list):
            listener_fn = tuple(listener_fn)
            local_listener_manager.add_listeners(*listener_fn)
        if isinstance(listener_fn, tuple):
            local_listener_manager.add_listeners(*listener_fn)
        #  just single listener function
        else:
            local_listener_manager.add_listener(listener_fn)
        return self

    def add_local_listener_manager(self, key, listener_manager):
        key_node = self.manager.get(key)
        if key_node is None:
            key_node = {}
        key_node["LISTENER_MANAGER"] = listener_manager
        return self

    def get_local_instances(self, key):
        if not self.manager.get(key):
            return None
        return self.manager.get(key).get("LOCAL_INSTANCES")

    def add_local_instance(self, slc):
        if not self.manager.get(slc.key):
            self.manager[slc.key] = {}
        if not self.manager.get(slc.key).get('LOCAL_INSTANCES'):
            self.manager.get(slc.key)['LOCAL_INSTANCES'] = {}
        self.manager.get(slc.key)['LOCAL_INSTANCES'][slc.instance_id] = slc
        return self

    def remove_local_instance(self, slc):
        key_node = self.manager.get(slc.key)
        if not key_node:
            return self
        local_instances_node = key_node.get("LOCAL_INSTANCES")
        if not local_instances_node:
            return self
        local_instance = local_instances_node.get(slc.instance_id)
        if not local_instance:
            return self
        local_instances_node.pop(slc.instance_id)
        return self


def parse_nacos_server_addr(server_addr):
    sp = server_addr.split(":")
    if len(sp) == 3:
        return sp[0] + ":" + sp[1], int(sp[2])
    else:
        port = int(sp[1]) if len(sp) > 1 else 8848
        return sp[0], port


class NacosClient:
    @staticmethod
    def get_md5(content):
        return hashlib.md5(content.encode("UTF-8")).hexdigest() if content is not None else None

    def get_server_from_url(self, url):
        server_list_content = urlopen(url, timeout=ADDRESS_SERVER_TIMEOUT).read()
        default_port = 8848
        server_list_temp = list()
        if server_list_content:
            for server_info in server_list_content.decode().strip().split("\n"):
                sp = server_info.strip().split(":")
                if len(sp) == 1:
                    # endpoint中没有指定port
                    server_list_temp.append((sp[0], default_port))
                else:
                    try:
                        port = sp.strip().split("/")[0]
                        server_list_temp.append((sp[0], int(port)))
                    except ValueError:
                        logger.warning(
                            "[get-server-list] bad server address:%s ignored" % server_info)
            if (self.server_list != server_list_temp):
                self.server_list = server_list_temp
        return server_list_temp

    def get_server_from_url_task(self, url):
        while (True):
            try:
                time.sleep(10)
                self.get_server_from_url(url)
            except Exception as ex:
                logger.exception("get_server_from_url_task %s" % ex)

    def initLog(self, logDir, log_level, log_rotation_backup_count):
        if logDir is None or logDir.strip() == "":
            logDir = os.path.expanduser("~") + "/logs/nacos/"
        if not logDir.endswith(os.path.sep):
            logDir += os.path.sep
        if not os.path.exists(logDir):
            os.makedirs(logDir)

        if log_rotation_backup_count is None:
            log_rotation_backup_count = 7
        log_path = logDir + 'nacos-client-python.log'
        if not logger.hasHandlers():
            file_handler = TimedRotatingFileHandler(log_path, when="midnight", interval=1,
                                                    backupCount=log_rotation_backup_count, encoding='utf-8')
            if log_level is not None:
                logger.setLevel(log_level)

            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logger.propagate = False

    def __init__(self, server_addresses=None, endpoint=None, namespace=None, ak=None,
                 sk=None, username=None, password=None, logDir=None, log_level=None, log_rotation_backup_count=None):
        self.server_list = list()
        self.initLog(logDir, log_level, log_rotation_backup_count)
        try:
            if server_addresses is not None and server_addresses.strip() != "":
                for server_addr in server_addresses.strip().split(","):
                    self.server_list.append(parse_nacos_server_addr(server_addr.strip()))
                logger.info("user server address  " + server_addresses)
            elif endpoint is not None and endpoint.strip() != "":
                url = endpoint.strip()
                if ("?" not in endpoint):
                    url = url + "?namespace=" + namespace
                else:
                    url = url + "&namespace=" + namespace
                logger.info("address server url " + url)
                self.get_server_from_url(url)
                partial_task_function = functools.partial(self.get_server_from_url_task,
                                                          url)
                thread = threading.Thread(target=partial_task_function)
                thread.daemon = True
                thread.start()
            else:
                logger.exception("[init] server address & endpoint must not both none")
                raise ValueError('server address & endpoint must not both none')
        except Exception as ex:
            logger.exception("[init] bad server address for %s" % server_addresses)
            raise ex

        self.current_server = self.server_list[0]

        self.endpoint = endpoint
        self.namespace = namespace or DEFAULT_NAMESPACE or ""
        self.ak = ak
        self.sk = sk
        self.username = username
        self.password = password

        self.token = None
        self.token_ttl = None  # token 的有效期（秒）
        self.token_expire_time = None

        self.server_list_lock = RLock()
        self.server_offset = 0

        self.watcher_mapping = dict()
        self.subscribed_local_manager = SubscribedLocalManager()
        self.subscribe_timer_manager = NacosTimerManager()
        self.pulling_lock = RLock()
        self.puller_mapping = None
        self.notify_queue = None
        self.callback_tread_pool = None
        self.process_mgr = None

        self.default_timeout = DEFAULTS["TIMEOUT"]
        self.auth_enabled = self.ak and self.sk
        self.cai_enabled = True
        self.pulling_timeout = DEFAULTS["PULLING_TIMEOUT"]
        self.pulling_config_size = DEFAULTS["PULLING_CONFIG_SIZE"]
        self.callback_thread_num = DEFAULTS["CALLBACK_THREAD_NUM"]
        self.failover_base = DEFAULTS["FAILOVER_BASE"]
        self.snapshot_base = DEFAULTS["SNAPSHOT_BASE"]
        self.no_snapshot = False
        self.proxies = None
        self.logDir = logDir

        self.heartbeats: Dict[str, HeartbeatTask] = {}
        if self.username and self.password:
            self.get_access_token()
        logger.info("[client-init] endpoint:%s, tenant:%s" % (endpoint, namespace))

    def set_options(self, **kwargs):
        for k, v in kwargs.items():
            if k not in OPTIONS:
                logger.warning("[set_options] unknown option:%s, ignored" % k)
                continue

            logger.debug("[set_options] key:%s, value:%s" % (k, v))
            setattr(self, k, v)

    def change_server(self):
        with self.server_list_lock:
            self.server_offset = (self.server_offset + 1) % len(self.server_list)
            self.current_server = self.server_list[self.server_offset]

    def get_server(self):
        logger.debug("[get-server] use server:%s" % str(self.current_server))
        return self.current_server

    def remove_config(self, data_id, group, timeout=None):
        data_id, group = process_common_config_params(data_id, group)
        logger.info(
            "[remove] data_id:%s, group:%s, namespace:%s, timeout:%s" % (data_id, group, self.namespace, timeout))

        params = {
            "dataId": data_id,
            "group": group,
        }
        if self.namespace:
            params["tenant"] = self.namespace

        try:
            resp = self._do_sync_req("/nacos/v1/cs/configs", None, params, None,
                                     timeout or self.default_timeout, "DELETE")
            c = resp.read()
            logger.info("[remove] remove group:%s, data_id:%s, server response:%s" % (
                group, data_id, c))
            return c == b"true"
        except HTTPError as e:
            if e.code == HTTPStatus.FORBIDDEN:
                logger.error(
                    "[remove] no right for namespace:%s, group:%s, data_id:%s" % (self.namespace, group, data_id))
                raise NacosException("Insufficient privilege.")
            else:
                logger.error("[remove] error code [:%s] for namespace:%s, group:%s, data_id:%s" % (
                    e.code, self.namespace, group, data_id))
                raise NacosException("Request Error, code is %s" % e.code)
        except Exception as e:
            logger.exception("[remove] exception %s occur" % str(e))
            raise

    def publish_config(self, data_id, group, content, app_name=None, config_type=None, timeout=None):
        if content is None:
            raise NacosException("Can not publish none content, use remove instead.")

        data_id, group = process_common_config_params(data_id, group)
        if type(content) == bytes:
            content = content.decode("UTF-8")

        logger.info("[publish] data_id:%s, group:%s, namespace:%s, content:%s, timeout:%s" % (
            data_id, group, self.namespace, truncate(content), timeout))

        params = {
            "dataId": data_id,
            "group": group,
            "content": content.encode("UTF-8"),
        }

        if self.namespace:
            params["tenant"] = self.namespace

        if app_name:
            params["appName"] = app_name

        if config_type:
            params["type"] = config_type

        try:
            resp = self._do_sync_req("/nacos/v1/cs/configs", None, params, None,
                                     timeout or self.default_timeout, "POST")
            c = resp.read()
            logger.info("[publish] publish content, group:%s, data_id:%s, server response:%s" % (
                group, data_id, c))
            return c == b"true"
        except HTTPError as e:
            if e.code == HTTPStatus.FORBIDDEN:
                logger.info(
                    "[publish] publish content fail result code :403, group:%s, data_id:%s" % (
                        group, data_id))
                raise NacosException("Insufficient privilege.")
            else:
                raise NacosException("Request Error, code is %s" % e.code)
        except Exception as e:
            logger.exception("[publish] exception %s occur" % str(e))
            raise

    def get_config(self, data_id, group, timeout=None, no_snapshot=None):
        no_snapshot = self.no_snapshot if no_snapshot is None else no_snapshot
        data_id, group = process_common_config_params(data_id, group)
        logger.debug("[get-config] data_id:%s, group:%s, namespace:%s, timeout:%s" % (
            data_id, group, self.namespace, timeout))

        params = {
            "dataId": data_id,
            "group": group,
        }
        if self.namespace:
            params["tenant"] = self.namespace

        cache_key = group_key(data_id, group, self.namespace)
        # get from failover
        content = read_file_str(self.failover_base, cache_key)
        if content is None:
            logger.debug("[get-config] failover config is not exist for %s, try to get from server" % cache_key)
        else:
            logger.debug("[get-config] get %s from failover directory, content is %s" % (cache_key, truncate(content)))
            return content

        # get from server
        try:
            resp = self._do_sync_req("/nacos/v1/cs/configs", None, params, None, timeout or self.default_timeout)
            content = resp.read().decode("UTF-8")
        except HTTPError as e:
            if e.code == HTTPStatus.NOT_FOUND:
                logger.warning(
                    "[get-config] config not found for data_id:%s, group:%s, namespace:%s, try to delete snapshot" % (
                        data_id, group, self.namespace))
                delete_file(self.snapshot_base, cache_key)
                return None
            elif e.code == HTTPStatus.CONFLICT:
                logger.error(
                    "[get-config] config being modified concurrently for data_id:%s, group:%s, namespace:%s" % (
                        data_id, group, self.namespace))
            elif e.code == HTTPStatus.FORBIDDEN:
                logger.error("[get-config] no right for data_id:%s, group:%s, namespace:%s" % (
                    data_id, group, self.namespace))
                raise NacosException("Insufficient privilege.")
            else:
                logger.error("[get-config] error code [:%s] for data_id:%s, group:%s, namespace:%s" % (
                    e.code, data_id, group, self.namespace))
                if no_snapshot:
                    raise
        except Exception as e:
            logger.exception("[get-config] exception %s occur" % str(e))
            if no_snapshot:
                raise

        if no_snapshot:
            return content

        if content is not None:
            logger.debug(
                "[get-config] content from server:%s, data_id:%s, group:%s, namespace:%s, try to save snapshot" % (
                    truncate(content), data_id, group, self.namespace))
            try:
                save_file(self.snapshot_base, cache_key, content)
            except Exception as e:
                logger.exception("[get-config] save snapshot failed for %s, data_id:%s, group:%s, namespace:%s" % (
                    data_id, group, self.namespace, str(e)))
            return content

        logger.info("[get-config] get config from server failed, try snapshot, data_id:%s, group:%s, namespace:%s" % (
            data_id, group, self.namespace))
        content = read_file_str(self.snapshot_base, cache_key)
        if content is None:
            logger.info("[get-config] snapshot is not exist for %s." % cache_key)
        else:
            logger.info("[get-config] get %s from snapshot directory, content is %s" % (cache_key, truncate(content)))
            return content

    def get_configs(self, timeout=None, no_snapshot=None, group="", page_no=1, page_size=1000):
        no_snapshot = self.no_snapshot if no_snapshot is None else no_snapshot
        logger.info("[get-configs] namespace:%s, timeout:%s, group:%s, page_no:%s, page_size:%s" % (
            self.namespace, timeout, group, page_no, page_size))

        params = {
            "dataId": "",
            "group": group,
            "search": "accurate",
            "pageNo": page_no,
            "pageSize": page_size,
        }
        if self.namespace:
            params["tenant"] = self.namespace

        cache_key = group_key("", "", self.namespace)
        # get from failover
        content = read_file_str(self.failover_base, cache_key)
        if content is None:
            logger.debug("[get-config] failover config is not exist for %s, try to get from server" % cache_key)
        else:
            logger.debug("[get-config] get %s from failover directory, content is %s" % (cache_key, truncate(content)))
            return json.loads(content)

        # get from server
        try:
            resp = self._do_sync_req("/nacos/v1/cs/configs", None, params, None, timeout or self.default_timeout)
            content = resp.read().decode("UTF-8")
        except HTTPError as e:
            if e.code == HTTPStatus.CONFLICT:
                logger.error(
                    "[get-configs] configs being modified concurrently for namespace:%s" % self.namespace)
            elif e.code == HTTPStatus.FORBIDDEN:
                logger.error("[get-configs] no right for namespace:%s" % self.namespace)
                raise NacosException("Insufficient privilege.")
            else:
                logger.error("[get-configs] error code [:%s] for namespace:%s" % (e.code, self.namespace))
                if no_snapshot:
                    raise
        except Exception as e:
            logger.exception("[get-config] exception %s occur" % str(e))
            if no_snapshot:
                raise

        if no_snapshot:
            return json.loads(content)

        if content is not None:
            logger.info(
                "[get-configs] content from server:%s, namespace:%s, try to save snapshot" % (
                    truncate(content), self.namespace))
            try:
                save_file(self.snapshot_base, cache_key, content)

                for item in json.loads(content).get("pageItems"):
                    data_id = item.get('dataId')
                    group = item.get('group')
                    item_content = item.get('content')
                    item_cache_key = group_key(data_id, group, self.namespace)
                    save_file(self.snapshot_base, item_cache_key, item_content)
            except Exception as e:
                logger.exception("[get-configs] save snapshot failed for %s, namespace:%s" % (
                    str(e), self.namespace))
            return json.loads(content)

        logger.error("[get-configs] get config from server failed, try snapshot, namespace:%s" % self.namespace)
        content = read_file_str(self.snapshot_base, cache_key)
        if content is None:
            logger.warning("[get-configs] snapshot is not exist for %s." % cache_key)
        else:
            logger.debug("[get-configs] get %s from snapshot directory, content is %s" % (cache_key, truncate(content)))
            return json.loads(content)

    @synchronized_with_attr("pulling_lock")
    def add_config_watcher(self, data_id, group, cb, content=None):
        self.add_config_watchers(data_id, group, [cb], content)

    @synchronized_with_attr("pulling_lock")
    def add_config_watchers(self, data_id, group, cb_list, content=None):
        if not cb_list:
            raise NacosException("A callback function is needed.")
        data_id, group = process_common_config_params(data_id, group)
        logger.info("[add-watcher] data_id:%s, group:%s, namespace:%s" % (data_id, group, self.namespace))
        cache_key = group_key(data_id, group, self.namespace)
        wl = self.watcher_mapping.get(cache_key)
        if not wl:
            wl = list()
            self.watcher_mapping[cache_key] = wl
        if not content:
            content = self.get_config(data_id, group)
        last_md5 = NacosClient.get_md5(content)
        for cb in cb_list:
            wl.append(WatcherWrap(cache_key, cb, last_md5))
            logger.info("[add-watcher] watcher has been added for key:%s, new callback is:%s, callback number is:%s" % (
                cache_key, cb.__name__, len(wl)))

        if self.puller_mapping is None:
            logger.debug("[add-watcher] pulling should be initialized")
            self._init_pulling()

        if cache_key in self.puller_mapping:
            logger.debug("[add-watcher] key:%s is already in pulling" % cache_key)
            return

        for key, puller_info in self.puller_mapping.items():
            if len(puller_info[1]) < self.pulling_config_size:
                logger.debug("[add-watcher] puller:%s is available, add key:%s" % (puller_info[0], cache_key))
                puller_info[1].append(cache_key)
                self.puller_mapping[cache_key] = puller_info
                break
        else:
            logger.debug("[add-watcher] no puller available, new one and add key:%s" % cache_key)
            key_list = self.process_mgr.list()
            key_list.append(cache_key)
            sys_os = platform.system()

            puller = Thread(target=self._do_pulling, args=(key_list, self.notify_queue))
            puller.setDaemon(True)

            puller.start()
            self.puller_mapping[cache_key] = (puller, key_list)

    @synchronized_with_attr("pulling_lock")
    def remove_config_watcher(self, data_id, group, cb, remove_all=False):
        if not cb:
            raise NacosException("A callback function is needed.")
        data_id, group = process_common_config_params(data_id, group)
        if not self.puller_mapping:
            logger.warning("[remove-watcher] watcher is never started.")
            return
        cache_key = group_key(data_id, group, self.namespace)
        wl = self.watcher_mapping.get(cache_key)
        if not wl:
            logger.warning("[remove-watcher] there is no watcher on key:%s" % cache_key)
            return

        wrap_to_remove = list()
        for i in wl:
            if i.callback == cb:
                wrap_to_remove.append(i)
                if not remove_all:
                    break

        for i in wrap_to_remove:
            wl.remove(i)

        logger.info("[remove-watcher] %s is removed from %s, remove all:%s" % (cb.__name__, cache_key, remove_all))
        if not wl:
            logger.debug("[remove-watcher] there is no watcher for:%s, kick out from pulling" % cache_key)
            self.watcher_mapping.pop(cache_key)
            puller_info = self.puller_mapping[cache_key]
            puller_info[1].remove(cache_key)
            if not puller_info[1]:
                logger.debug("[remove-watcher] there is no pulling keys for puller:%s, stop it" % puller_info[0])
                self.puller_mapping.pop(cache_key)
                if isinstance(puller_info[0], Process):
                    puller_info[0].terminate()

    def _do_sync_req(self, url, headers=None, params=None, data=None, timeout=None, method="GET", module="config"):
        all_headers = {}
        if headers:
            all_headers.update(headers)
        all_params = {}
        if params:
            all_params.update(params)
        self._inject_version_info(all_headers)
        self._inject_auth_info(all_headers, all_params, data, module)
        url = "?".join([url, urlencode(all_params)]) if all_params else url
        logger.debug(
            "[do-sync-req] url:%s, headers:%s, params:%s, data:%s, timeout:%s" % (
                url, all_headers, all_params, data, timeout))
        tries = 0
        while True:
            try:
                server_info = self.get_server()
                if not server_info:
                    logger.error("[do-sync-req] can not get one server.")
                    raise NacosRequestException("Server is not available.")
                address, port = server_info
                server = ":".join([address, str(port)])
                server_url = server
                if not server_url.startswith("http"):
                    server_url = "%s://%s" % ("http", server)
                if python_version_bellow("3"):
                    req = Request(url=server_url + url, data=urlencode(data).encode() if data else None,
                                  headers=all_headers)
                    req.get_method = lambda: method
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                else:
                    req = Request(url=server_url + url, data=urlencode(data).encode() if data else None,
                                  headers=all_headers, method=method)
                    ctx = ssl.SSLContext()
                # build a new opener that adds proxy setting so that http request go through the proxy
                if self.proxies:
                    proxy_support = ProxyHandler(self.proxies)
                    https_support = HTTPSHandler(context=ctx)
                    opener = build_opener(proxy_support, https_support)
                    resp = opener.open(req, timeout=timeout)
                else:
                    # for python version compatibility
                    if python_version_bellow("2.7.5"):
                        resp = urlopen(req, timeout=timeout)
                    else:
                        resp = urlopen(req, timeout=timeout, context=ctx)
                logger.debug("[do-sync-req] info from server:%s" % server)
                return resp
            except HTTPError as e:
                if e.code in [HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.BAD_GATEWAY,
                              HTTPStatus.SERVICE_UNAVAILABLE]:
                    logger.warning("[do-sync-req] server:%s is not available for reason:%s" % (server, e.msg))
                else:
                    raise
            except socket.timeout:
                logger.warning("[do-sync-req] %s request timeout" % server)
            except URLError as e:
                logger.warning("[do-sync-req] %s connection error:%s" % (server, e.reason))

            tries += 1
            if tries >= len(self.server_list):
                logger.error("[do-sync-req] %s maybe down, no server is currently available" % server)
                raise NacosRequestException("All server are not available")
            self.change_server()
            logger.warning("[do-sync-req] %s maybe down, skip to next" % server)

    def _do_pulling(self, cache_list, queue):
        cache_pool = dict()
        for cache_key in cache_list:
            cache_pool[cache_key] = CacheData(cache_key, self)

        while cache_list:
            unused_keys = set(cache_pool.keys())
            contains_init_key = False
            probe_update_string = ""
            for cache_key in cache_list:
                cache_data = cache_pool.get(cache_key)
                if not cache_data:
                    logger.debug("[do-pulling] new key added: %s" % cache_key)
                    cache_data = CacheData(cache_key, self)
                    cache_pool[cache_key] = cache_data
                else:
                    unused_keys.remove(cache_key)
                if cache_data.is_init:
                    contains_init_key = True
                data_id, group, namespace = parse_key(cache_key)
                probe_update_string += WORD_SEPARATOR.join(
                    [data_id, group, cache_data.md5 or "", self.namespace]) + LINE_SEPARATOR

            for k in unused_keys:
                logger.debug("[do-pulling] %s is no longer watched, remove from cache" % k)
                cache_pool.pop(k)

            logger.debug(
                "[do-pulling] try to detected change from server probe string is %s" % truncate(probe_update_string))
            headers = {"Long-Pulling-Timeout": int(self.pulling_timeout * 1000)}
            # if contains_init_key:
            #     headers["longPullingNoHangUp"] = "true"

            data = {"Listening-Configs": probe_update_string}

            changed_keys = list()
            try:
                resp = self._do_sync_req("/nacos/v1/cs/configs/listener", headers, None, data,
                                         self.pulling_timeout + 10, "POST")
                changed_keys = [group_key(*i) for i in parse_pulling_result(resp.read())]
                logger.info("[do-pulling] following keys are changed from server %s" % truncate(str(changed_keys)))
            except NacosException as e:
                logger.error("[do-pulling] nacos exception: %s, waiting for recovery" % str(e))
                time.sleep(1)
            except Exception as e:
                logger.exception("[do-pulling] exception %s occur, return empty list, waiting for recovery" % str(e))
                time.sleep(1)

            for cache_key, cache_data in cache_pool.items():
                cache_data.is_init = False
                if cache_key in changed_keys:
                    data_id, group, namespace = parse_key(cache_key)
                    content = self.get_config(data_id, group)
                    cache_data.md5 = NacosClient.get_md5(content)
                    cache_data.content = content
                queue.put((cache_key, cache_data.content, cache_data.md5))

    @synchronized_with_attr("pulling_lock")
    def _init_pulling(self):
        if self.puller_mapping is not None:
            logger.info("[init-pulling] puller is already initialized")
            return
        self.puller_mapping = dict()
        self.notify_queue = Queue()
        self.callback_tread_pool = pool.ThreadPool(self.callback_thread_num)
        self.process_mgr = Manager()
        t = Thread(target=self._process_polling_result)
        t.setDaemon(True)
        t.start()
        logger.info("[init-pulling] init completed")

    def _process_polling_result(self):
        while True:
            cache_key, content, md5 = self.notify_queue.get()
            logger.info("[process-polling-result] receive an event:%s" % cache_key)
            wl = self.watcher_mapping.get(cache_key)
            if not wl:
                logger.warning("[process-polling-result] no watcher on %s, ignored" % cache_key)
                continue

            data_id, group, namespace = parse_key(cache_key)
            plain_content = content

            params = {
                "data_id": data_id,
                "group": group,
                "namespace": namespace,
                "raw_content": content,
                "content": plain_content,
            }
            for watcher in wl:
                if not watcher.last_md5 == md5:
                    logger.info(
                        "[process-polling-result] md5 changed since last call, calling %s with changed md5: %s ,params: %s"
                        % (watcher.callback.__name__, md5, params))
                    try:
                        self.callback_tread_pool.apply(watcher.callback, (params,))
                    except Exception as e:
                        logger.exception("[process-polling-result] exception %s occur while calling %s " % (
                            str(e), watcher.callback.__name__))
                    watcher.last_md5 = md5

    @staticmethod
    def _inject_version_info(headers):
        headers.update({"User-Agent": "Nacos-Python-Client:v" + VERSION})

    def get_access_token(self, force_refresh=False):
        current_time = time.time()
        if self.token and not force_refresh and self.token_expire_time > current_time:
            return self.token

        params = {
            "username": self.username,
            "password": self.password
        }
        try:
            resp = self._do_sync_req("/nacos/v1/auth/login", None, params, None, self.default_timeout, "POST", "login")
            c = resp.read()
            response_data = json.loads(c.decode("UTF-8"))
            self.token = response_data.get('accessToken')
            self.token_ttl = response_data.get('tokenTtl', 18000)  # 默认使用返回值，无返回则使用18000秒
            self.token_expire_time = current_time + self.token_ttl - 10  # 更新 Token 的过期时间
            logger.info(
                f"[get_access_token] AccessToken: {self.token}, TTL: {self.token_ttl}，force_refresh：{force_refresh}")
        except Exception as e:
            logger.exception("[get-access-token] exception %s occur" % str(e))
            raise

    def _inject_auth_info(self, headers, params, data, module="config"):
        if module == 'login':
            return

        if self.username and self.password:
            self.get_access_token(force_refresh=False)
            params["accessToken"] = self.token

        if not self.auth_enabled:
            return

        # in case tenant or group is null
        if not params and not data:
            return
        ts = str(int(time.time() * 1000))
        ak, sk = self.ak, self.sk

        sign_str = ""

        params_to_sign = params or data or {}
        # config signature
        if "config" == module:
            headers.update({
                "Spas-AccessKey": ak,
                "timeStamp": ts,
            })

            tenant = params_to_sign.get("tenant")
            group = params_to_sign.get("group")

            if tenant:
                sign_str = tenant + "+"
            if group:
                sign_str = sign_str + group + "+"
            if sign_str:
                sign_str += ts
                headers["Spas-Signature"] = self.__do_sign(sign_str, sk)

        # naming signature
        else:
            group = params_to_sign.get("groupName")
            service_name = params_to_sign.get("serviceName")

            if service_name:
                if "@@" in service_name or group is None or group == "":
                    sign_str = service_name
                else:
                    sign_str = group + "@@" + service_name
                sign_str = ts + "@@" + sign_str
            else:
                sign_str = ts

            params.update({
                "ak": ak,
                "data": sign_str,
                "signature": self.__do_sign(sign_str, sk),
            })

    def __do_sign(self, sign_str, sk):
        return base64.encodebytes(
            hmac.new(sk.encode(), sign_str.encode(), digestmod=hashlib.sha1).digest()).decode().strip()

    def _build_metadata(self, metadata, params):
        if metadata:
            if isinstance(metadata, dict):
                params["metadata"] = json.dumps(metadata)
            else:
                params["metadata"] = metadata

    def add_naming_instance(self, service_name, ip, port, cluster_name=None, weight=1.0, metadata=None,
                            enable=True, healthy=True, ephemeral=True, group_name=DEFAULT_GROUP_NAME,
                            heartbeat_interval=None):
        logger.info("[add-naming-instance] ip:%s, port:%s, service_name:%s, namespace:%s" % (
            ip, port, service_name, self.namespace))

        params = {
            "ip": ip,
            "port": port,
            "serviceName": service_name,
            "weight": weight,
            "enable": enable,
            "healthy": healthy,
            "clusterName": cluster_name,
            "ephemeral": ephemeral,
            "groupName": group_name
        }
        self._build_metadata(metadata, params)

        if self.namespace:
            params["namespaceId"] = self.namespace

        try:
            resp = self._do_sync_req("/nacos/v1/ns/instance", None, params, None, self.default_timeout, "POST",
                                     "naming")
            c = resp.read()
            logger.info("[add-naming-instance] ip:%s, port:%s, service_name:%s, namespace:%s, server response:%s" % (
                ip, port, service_name, self.namespace, c))
            result = c == b"ok"

            if result and ephemeral and heartbeat_interval is not None:
                beat_info = HeartbeatInfo(service_name, ip, port, cluster_name, group_name, weight, heartbeat_interval,
                                          metadata)
                self.__add_naming_heartbeat(service_name, beat_info)
            return result
        except HTTPError as e:
            if e.code == HTTPStatus.FORBIDDEN:
                raise NacosException("Insufficient privilege.")
            else:
                raise NacosException("Request Error, code is %s" % e.code)
        except Exception as e:
            logger.exception("[add-naming-instance] exception %s occur" % str(e))
            raise

    def __add_naming_heartbeat(self, service_name, beat_info: HeartbeatInfo):
        beat_info_key = "%s#%s#%s" % (service_name, beat_info.ip, beat_info.port)
        exist_task = self.heartbeats.get(beat_info_key)
        if exist_task:
            exist_task.stop()

        new_task = HeartbeatTask(beat_info=beat_info, client=self)
        new_task.start()
        self.heartbeats[beat_info_key] = new_task

    def remove_naming_instance(self, service_name, ip, port, cluster_name=None, ephemeral=True,
                               group_name=DEFAULT_GROUP_NAME):
        logger.info("[remove-naming-instance] ip:%s, port:%s, service_name:%s, namespace:%s" % (
            ip, port, service_name, self.namespace))

        params = {
            "ip": ip,
            "port": port,
            "serviceName": service_name,
            "ephemeral": ephemeral,
            "groupName": group_name
        }

        if cluster_name is not None:
            params["clusterName"] = cluster_name

        if self.namespace:
            params["namespaceId"] = self.namespace

        try:
            resp = self._do_sync_req("/nacos/v1/ns/instance", None, params, None, self.default_timeout, "DELETE",
                                     "naming")
            c = resp.read()
            logger.info("[remove-naming-instance] ip:%s, port:%s, service_name:%s, namespace:%s, server response:%s" % (
                ip, port, service_name, self.namespace, c))
            if ephemeral:
                beat_info_key = "%s#%s#%s" % (service_name, ip, port)
                exist_task = self.heartbeats.get(beat_info_key)
                if exist_task:
                    exist_task.stop()
            return c == b"ok"
        except HTTPError as e:
            if e.code == HTTPStatus.FORBIDDEN:
                raise NacosException("Insufficient privilege.")
            else:
                raise NacosException("Request Error, code is %s" % e.code)
        except Exception as e:
            logger.exception("[remove-naming-instance] exception %s occur" % str(e))
            raise

    def modify_naming_instance(self, service_name, ip, port, cluster_name=None, weight=None, metadata=None,
                               enable=None, ephemeral=True, group_name=DEFAULT_GROUP_NAME):
        logger.info("[modify-naming-instance] ip:%s, port:%s, service_name:%s, namespace:%s" % (
            ip, port, service_name, self.namespace))

        params = {
            "ip": ip,
            "port": port,
            "serviceName": service_name,
            "ephemeral": ephemeral,
            "groupName": group_name
        }

        if cluster_name is not None:
            params["clusterName"] = cluster_name

        if enable is not None:
            params["enable"] = enable

        if weight is not None:
            params["weight"] = weight

        self._build_metadata(metadata, params)

        if self.namespace:
            params["namespaceId"] = self.namespace

        try:
            resp = self._do_sync_req("/nacos/v1/ns/instance", None, params, None, self.default_timeout, "PUT", "naming")
            c = resp.read()
            logger.info("[modify-naming-instance] ip:%s, port:%s, service_name:%s, namespace:%s, server response:%s" % (
                ip, port, service_name, self.namespace, c))
            return c == b"ok"
        except HTTPError as e:
            if e.code == HTTPStatus.FORBIDDEN:
                raise NacosException("Insufficient privilege.")
            else:
                raise NacosException("Request Error, code is %s" % e.code)
        except Exception as e:
            logger.exception("[modify-naming-instance] exception %s occur" % str(e))
            raise

    def list_naming_instance(self, service_name, clusters=None, namespace_id=None, group_name=None, healthy_only=False):
        """
        :param service_name:        服务名
        :param clusters:            集群名称            字符串，多个集群用逗号分隔
        :param namespace_id:        命名空间ID
        :param group_name:          分组名
        :param healthy_only:         是否只返回健康实例   否，默认为false
        """
        logger.info("[list-naming-instance] service_name:%s, namespace:%s" % (service_name, self.namespace))

        params = {
            "serviceName": service_name,
            "healthyOnly": healthy_only
        }

        if clusters is not None:
            params["clusters"] = clusters

        namespace_id = namespace_id or self.namespace
        if namespace_id:
            params["namespaceId"] = namespace_id

        group_name = group_name or 'DEFAULT_GROUP'
        if group_name:
            params['groupName'] = group_name

        try:
            resp = self._do_sync_req("/nacos/v1/ns/instance/list", None, params, None, self.default_timeout, "GET",
                                     "naming")
            c = resp.read()
            logger.info("[list-naming-instance] service_name:%s, namespace:%s, server response:%s" %
                        (service_name, self.namespace, c))
            return json.loads(c.decode("UTF-8"))
        except HTTPError as e:
            if e.code == HTTPStatus.FORBIDDEN:
                raise NacosException("Insufficient privilege.")
            else:
                raise NacosException("Request Error, code is %s" % e.code)
        except Exception as e:
            logger.exception("[list-naming-instance] exception %s occur" % str(e))
            raise

    def get_naming_instance(self, service_name, ip, port, cluster_name=None):
        logger.info("[get-naming-instance] ip:%s, port:%s, service_name:%s, namespace:%s" % (ip, port, service_name,
                                                                                             self.namespace))

        params = {
            "serviceName": service_name,
            "ip": ip,
            "port": port,
        }

        if cluster_name is not None:
            params["cluster"] = cluster_name
            params["clusterName"] = cluster_name

        if self.namespace:
            params["namespaceId"] = self.namespace

        try:
            resp = self._do_sync_req("/nacos/v1/ns/instance", None, params, None, self.default_timeout, "GET", "naming")
            c = resp.read()
            logger.info("[get-naming-instance] ip:%s, port:%s, service_name:%s, namespace:%s, server response:%s" %
                        (ip, port, service_name, self.namespace, c))
            return json.loads(c.decode("UTF-8"))
        except HTTPError as e:
            if e.code == HTTPStatus.FORBIDDEN:
                raise NacosException("Insufficient privilege.")
            else:
                raise NacosException("Request Error, code is %s" % e.code)
        except Exception as e:
            logger.exception("[get-naming-instance] exception %s occur" % str(e))
            raise

    def send_heartbeat(self, service_name, ip, port, cluster_name=None, weight=1.0, metadata=None, ephemeral=True,
                       group_name=DEFAULT_GROUP_NAME):
        logger.info("[send-heartbeat] ip:%s, port:%s, service_name:%s, namespace:%s" % (ip, port, service_name,
                                                                                        self.namespace))
        beat_data = {
            "serviceName": service_name,
            "ip": ip,
            "port": port,
            "weight": weight,
            "ephemeral": ephemeral

        }

        if cluster_name is not None:
            beat_data["cluster"] = cluster_name

        if metadata is not None:
            if isinstance(metadata, str):
                beat_data["metadata"] = json.loads(metadata)
            else:
                beat_data["metadata"] = metadata

        params = {
            "serviceName": service_name,
            "beat": json.dumps(beat_data),
            "groupName": group_name
        }

        if self.namespace:
            params["namespaceId"] = self.namespace

        try:
            resp = self._do_sync_req("/nacos/v1/ns/instance/beat", None, params, None, self.default_timeout, "PUT",
                                     "naming")
            c = resp.read()
            logger.info("[send-heartbeat] ip:%s, port:%s, service_name:%s, namespace:%s, server response:%s" %
                        (ip, port, service_name, self.namespace, c))
            return json.loads(c.decode("UTF-8"))
        except HTTPError as e:
            if e.code == HTTPStatus.FORBIDDEN:
                raise NacosException("Insufficient privilege.")
            else:
                raise NacosException("Request Error, code is %s" % e.code)
        except Exception as e:
            logger.exception("[send-heartbeat] exception %s occur" % str(e))
            raise

    def subscribe(self,
                  listener_fn, listener_interval=7, *args, **kwargs):
        """
        reference at `/nacos/v1/ns/instance/list` in https://nacos.io/zh-cn/docs/open-api.html
        :param listener_fn           监听方法，可以是元组，列表，单个监听方法
        :param listener_interval     监听间隔，在 HTTP 请求 OpenAPI 时间间隔
        :return:
        """
        service_name = kwargs.get("service_name")
        if not service_name:
            if len(args) > 0:
                service_name = args[0]
            else:
                raise NacosException("`service_name` is required in subscribe")
        self.subscribed_local_manager.add_local_listener(key=service_name, listener_fn=listener_fn)

        #  判断是否是第一次订阅调用
        class _InnerSubContext(object):
            first_sub = True

        def _compare_and_trigger_listener():
            #  invoke `list_naming_instance`
            latest_res = self.list_naming_instance(*args, **kwargs)
            latest_instances = latest_res['hosts']
            #  获取本地缓存实例
            local_service_instances_dict = self.subscribed_local_manager.get_local_instances(service_name)
            #  当前本地没有缓存，所有都是新的实例
            if not local_service_instances_dict:
                if not latest_instances or len(latest_instances) < 1:
                    #  第一次订阅调用不通知
                    if _InnerSubContext.first_sub:
                        _InnerSubContext.first_sub = False
                        return
                for instance in latest_instances:
                    slc = SubscribedLocalInstance(key=service_name, instance=instance)
                    self.subscribed_local_manager.add_local_instance(slc)
                    #  第一次订阅调用不通知
                    if _InnerSubContext.first_sub:
                        _InnerSubContext.first_sub = False
                        return
                    self.subscribed_local_manager.do_listener_launch(service_name, Event.ADDED, slc)
            else:
                local_service_instances_dict_copy = local_service_instances_dict.copy()
                for instance in latest_instances:
                    slc = SubscribedLocalInstance(key=service_name, instance=instance)
                    local_slc = local_service_instances_dict.get(slc.instance_id)
                    # 本地不存在实例缓存
                    if local_slc is None:
                        self.subscribed_local_manager.add_local_instance(slc)
                        self.subscribed_local_manager.do_listener_launch(service_name, Event.ADDED, slc)
                    # 本地存在实例缓存
                    else:
                        local_slc_md5 = local_slc.md5
                        local_slc_id = local_slc.instance_id
                        local_service_instances_dict_copy.pop(local_slc_id)
                        # 比较md5,存在实例变更
                        if local_slc_md5 != slc.md5:
                            self.subscribed_local_manager.remove_local_instance(local_slc).add_local_instance(slc)
                            self.subscribed_local_manager.do_listener_launch(service_name, Event.MODIFIED, slc)
                #  still have instances in local marked deleted
                if len(local_service_instances_dict_copy) > 0:
                    for local_slc_id, slc in local_service_instances_dict_copy.items():
                        self.subscribed_local_manager.remove_local_instance(slc)
                        self.subscribed_local_manager.do_listener_launch(service_name, Event.DELETED, slc)

        timer_name = 'service-subscribe-timer-{key}'.format(key=service_name)
        subscribe_timer = NacosTimer(name=timer_name,
                                     interval=listener_interval,
                                     fn=_compare_and_trigger_listener)
        subscribe_timer.scheduler()
        self.subscribe_timer_manager.add_timer(subscribe_timer)

    def unsubscribe(self, service_name, listener_name=None):
        """
        remove listener from subscribed  listener manager
        :param service_name:    service_name
        :param listener_name:   listener name
        :return: 
        """
        listener_manager = self.subscribed_local_manager.get_local_listener_manager(key=service_name)
        if not listener_manager:
            return
        if listener_name:
            listener_manager.remove_listener(listener_name)
            return
        listener_manager.empty_listeners()

    def stop_subscribe(self):
        """
        stop subscribe timer scheduler
        :return: 
        """
        self.subscribe_timer_manager.stop()