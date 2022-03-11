import hashlib
from concurrent.futures import ThreadPoolExecutor

from v2.nacos.common.constants import Constants
from v2.nacos.config.filter_impl.config_response import ConfigResponse
from v2.nacos.config.impl.local_config_info_processor import LocalConfigInfoProcessor
from v2.nacos.config.impl.local_encrypted_data_key_processor import LocalEncryptedDataKeyProcessor
from v2.nacos.exception.nacos_exception import NacosException


class CacheData:
    PER_TASK_CONFIG_SIZE = 3000

    CONCURRENCY = 5

    def __init__(self, logger, config_filter_chain_manager, name, data_id, group, tenant):
        if not data_id or not group:
            raise NacosException("[ArgumentNullException] dataId=" + data_id + ", group=" + group)

        self.logger = logger
        self.name = name
        self.config_filter_chain_manager = config_filter_chain_manager
        self.data_id = data_id
        self.group = group
        self.tenant = tenant
        self.listeners = []
        self.is_initializing = True
        self.content = self.__load_cache_content_from_disk_local(name, data_id, group, tenant)
        self.md5 = self.get_md5_str(self.content)

        self.use_local_config = False
        self.local_config_last_modified = None

        self.encrypted_data_key = self.__load_encrypted_data_key_from_disk_local(name, data_id, group, tenant)
        self.last_modified_ts = 0
        self.task_id = None
        self.initializing = True
        self.sync_with_server = False
        self.type = None

        self.INTERNAL_NOTIFIER = ThreadPoolExecutor(max_workers=CacheData.CONCURRENCY)

    def is_initializing(self) -> bool:
        return self.initializing

    def set_initializing(self, initializing: bool) -> None:
        self.initializing = initializing

    def get_md5(self) -> str:
        return self.md5

    def get_tenant(self) -> str:
        return self.tenant

    def get_content(self) -> str:
        return self.content

    def set_content(self, content: str) -> None:
        self.content = content
        self.md5 = self.get_md5_str(content)

    def get_last_modified_ts(self) -> int:
        return self.last_modified_ts

    def set_last_modified_ts(self, last_modified_ts: int):
        self.last_modified_ts = last_modified_ts

    def get_type(self) -> type:
        return self.type

    def set_type(self, config_type) -> None:
        self.type = config_type

    def add_listener(self, listener) -> None:
        if not listener:
            raise NacosException("[ArgumentException]Listener is None")
        wrap = CacheData.ManagerListenerWrap(listener=listener, md5=self.md5, last_content=self.content)
        self.listeners.append(wrap)
        self.logger.info("[%s][add-listener] ok, tenant=%s, dataId=%s, group=%s, cnt=%s"
                         % (self.name, self.tenant, self.data_id, self.group, len(self.listeners))
                         )

    def remove_listener(self, listener) -> None:
        if not listener:
            raise NacosException("[ArgumentException]Listener is None")
        try:
            for listener_wrap in self.listeners:
                if listener_wrap.listener is listener:
                    self.listeners.remove(listener_wrap)
            self.logger.info("[%s][remove-listener] ok, dataId=%s, group=%s, cnt=%s"
                             % (self.name, self.data_id, self.group, len(self.listeners)))
        except NacosException as e:
            pass

    def get_listeners(self) -> list:
        result = []
        for wrap in self.listeners:
            result.append(wrap.listener)
        return result

    def set_local_config_info_version(self, local_config_last_modified: int) -> None:
        self.local_config_last_modified = local_config_last_modified

    def get_local_config_info_version(self) -> int:
        return self.local_config_last_modified

    def set_use_local_config_info(self, use_local_config_info: bool) -> None:
        self.use_local_config = use_local_config_info
        if not use_local_config_info:
            self.local_config_last_modified = -1

    def is_use_local_config_info(self) -> bool:
        return self.use_local_config

    def get_task_id(self) -> int:
        return self.task_id

    def set_task_id(self, task_id: int) -> None:
        self.task_id = task_id

    def get_hash_code(self) -> int:
        prime = 31
        result = 1
        result = prime * result
        result += 0 if not self.data_id else hash(self.data_id)
        result += 0 if not self.group else hash(self.group)
        return result

    def __str__(self):
        return "CacheData [" + self.data_id + ", " + self.group + "]"

    def check_listener_md5(self) -> None:
        for wrap in self.listeners:
            if wrap.last_call_md5 != self.md5:
                self.__safe_notify_listener(
                    self.data_id, self.group, self.content, self.type, self.md5, self.encrypted_data_key, wrap
                )

    def check_listener_md5_consistent(self) -> bool:
        for wrap in self.listeners:
            if self.md5 != wrap.last_call_md5:
                return False

    def __safe_notify_listener(
            self, data_id, group, content, config_type, md5, encrypted_dat_key, listener_wrap) -> None:
        # todo
        # def job():
        #     start = get_current_time_millis()
        #     try:
        #         if isinstance(listener, AbstractSharedListener):
        #             listener.fill_context(data_id, group)
        #             self.logger.info("[%s] [notify-context] dataId=%s, group=%s, md5=%s"
        #                              % (self.name, data_id, group, md5))
        #
        #             cr = ConfigResponse()
        #             cr.set_data_id(data_id)
        #             cr.set_group(group)
        #             cr.set_content(content)
        #             cr.set_encrypted_data_key(encrypted_dat_key)
        #             self.config_filter_chain_manager.do_filter(None, cr)
        #             content_tmp = cr.get_content()
        #             listener_wrap.in_notifying = True
        #             listener.receive_config_info(content_tmp)
        #
        #         if isinstance(listener, AbstractConfigChangeListener):
        #             data = ConfigChangeHandler.get_instance().parse_change_data(
        #                 listener_wrap.last_content, content, config_type
        #             )
        #             event = ConfigChangeEvent(data)
        #             listener.receive_config_change(event)
        #             listener_wrap.last_content = content
        #
        #         listener_wrap = md5
        #
        #         self.logger.info("[%s] [notify-ok] dataId=%s, group=%s, md5=%s, listener=%s, cost=%s millis."
        #                          % (self.name, data_id, group, md5, listener, str(get_current_time_millis() - start)))
        #     except NacosException as ex:
        #         self.logger.error("[%s] [notify-error] dataId=%s, group=%s, md5=%s, listener=%s, errInfo=%s"
        #                           % (self.name, data_id, group, md5, listener, str(ex)))
        #     finally:
        #         listener_wrap.in_notifying = False
        #
        # listener = listener_wrap.listener
        # if listener_wrap.in_notifying:
        #     self.logger.warning("[%s] [notify-currentSkip] dataId=%s, group=%s, md5=%s, listener=%s, "
        #                         % (self.name, data_id, group, md5, listener) +
        #                         "listener is not finish yet, will try next time."
        #                         )
        #
        # start_notify = get_current_time_millis()
        # try:
        #     if listener.get_executor():
        #         listener.get_executor.submit(job)
        #     else:
        #         try:
        #             self.INTERNAL_NOTIFIER.submit(job)
        #         except NacosException as e:
        #             self.logger.error("[%s] [notify-blocked] dataId=%s, group=%s, md5=%s, listener=%s"
        #                               % (self.name, data_id, group, md5, listener)
        #                               )
        #             # if there is an exception, run in order
        #             job()
        # except NacosException as e:
        #     self.logger.error("[%s] [notify-error] dataId=%s, group=%s, md5=%s, listener=%s: %s"
        #                       % (self.name, data_id, group, md5, listener, str(e))
        #                       )
        # finish_notify = get_current_time_millis()
        # self.logger.info(
        #     "[%s] [notify-listener] time cost=%sms in ClientWorker, dataId=%s, group=%s, md5=%s, listener=%s"
        #     % (self.name, str(finish_notify-start_notify), data_id, group, md5, listener)
        # )

        listener = listener_wrap.listener
        cr = ConfigResponse()
        cr.set_data_id(data_id)
        cr.set_group(group)
        cr.set_content(content)
        cr.set_encrypted_data_key(encrypted_dat_key)
        self.config_filter_chain_manager.do_filter(None, cr)

        content_tmp = cr.get_content()

        listener_wrap.last_content = content
        listener_wrap.last_call_md5 = md5

        listener.receive_config_info(content_tmp)

    @staticmethod
    def get_md5_str(config: str) -> str:
        if not config:
            return Constants.NULL
        else:
            md5 = hashlib.md5()
            md5.update(config.encode("utf-8"))
            return md5.hexdigest()

    def __load_cache_content_from_disk_local(self, name: str, data_id: str, group: str, tenant: str) -> str:
        local_config_info_processor = LocalConfigInfoProcessor(self.logger)
        content = local_config_info_processor.get_failover(name, data_id, group, tenant)
        if not content:
            content = local_config_info_processor.get_snapshot(name, data_id, group, tenant)
        return content

    def is_sync_with_server(self) -> bool:
        return self.sync_with_server

    def set_sync_with_server(self, sync_with_server: bool) -> None:
        self.sync_with_server = sync_with_server

    def get_encrypted_data_key(self) -> str:
        return self.encrypted_data_key

    def set_encrypted_data_key(self, encrypted_data_key: str) -> None:
        self.encrypted_data_key = encrypted_data_key

    def __load_encrypted_data_key_from_disk_local(self, name: str, data_id: str, group: str, tenant: str) -> str:
        local_encrypted_data_key_processor = LocalEncryptedDataKeyProcessor(self.logger)
        encrypted_data_key = local_encrypted_data_key_processor.get_encrypt_data_key_failover(
            name, data_id, group, tenant
        )

        if encrypted_data_key:
            return encrypted_data_key

        return local_encrypted_data_key_processor.get_encrypt_data_key_snapshot(name, data_id, group, tenant)

    class ManagerListenerWrap:
        def __init__(self, listener=None, md5=None, last_content=None):
            self.listener = listener
            self.last_call_md5 = md5
            self.last_content = last_content

            self.in_notifying = False
