import logging
import sched
import time
from concurrent.futures import ThreadPoolExecutor

from v2.nacos.common.nacos_exception import NacosException, ErrorCode
from v2.nacos.config.client_config import ClientConfig
from v2.nacos.naming.cache.service_info_cache import ServiceInfoCache
from v2.nacos.naming.model.instance import Instance
from v2.nacos.naming.remote.grpc.naming_grpc_client_proxy import NamingGrpcClientProxy
from v2.nacos.naming.remote.http.naming_http_client_proxy import NamingHttpClientProxy
from v2.nacos.naming.util.naming_client_util import *
from v2.nacos.naming.remote.naming_client_proxy import NamingClientProxy


class NamingClientProxyDelegate(NamingClientProxy):
    def __init__(self, client_config: ClientConfig, service_info_cache: ServiceInfoCache, properties, change_notifier):
        self.logger = logging.getLogger(__name__)

        self.security_info_refresh_interval_second = 5
        self.service_info_update_service = ServiceInfoUpdateService(properties, service_info_holder,
                                                                    self, change_notifier)
        self.server_list_manager = ServerListManager(properties)
        self.service_info_cache = service_info_cache
        self.security_proxy = SecurityProxy(properties)
        self.__init_security_proxy()

        self.http_client_proxy = NamingHttpClientProxy(namespace, self.security_proxy,
                                                       self.server_list_manager, properties, service_info_cache)
        self.grpc_client_proxy = NamingGrpcClientProxy(namespace, self.security_proxy, self.server_list_manager,
                                                       properties, service_info_cache)

    def __init_security_proxy(self):
        self.login_timer = sched.scheduler(time.time, time.sleep)
        self.login_timer.enter(self.security_info_refresh_interval_second, 0, self.security_proxy.login,
                               (self.server_list_manager.get_server_list(),))
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.executor.submit(self.login_timer.run)

    def register_instance(self, service_name: str, group_name: str, instance: Instance) -> bool:
        return self.__get_execute_client_proxy(instance).register_instance(service_name, group_name, instance)

    def batch_register_instance(self, service_name: str, group_name: str, instances: list[Instance]) -> bool:
        return self.grpc_client_proxy.batch_register_instance(service_name, group_name, instances)

    def deregister_instance(self, service_name: str, group_name: str, instance: Instance):
        return self.__get_execute_client_proxy(instance).deregister_instance(service_name, group_name, instance)

    def get_service_list(self, page_no: int, page_size: int, group_name: str, namespace_id: str, selector):
        return self.grpc_client_proxy.get_service_list(page_no, page_size, group_name, namespace_id, selector)

    def server_healthy(self):
        return self.grpc_client_proxy.server_healthy() or self.http_client_proxy.server_healthy()

    def query_instances_of_service(self, service_name: str, group_name: str, clusters: str, udp_port: int,
                                   healthy_only: bool):
        return self.grpc_client_proxy.query_instances_of_service(service_name, group_name, clusters, udp_port,
                                                                 healthy_only)

    def subscribe(self, service_name: str, group_name: str, clusters: str):
        is_subscribed = self.grpc_client_proxy.is_subscribed(service_name, group_name, clusters)
        service_name_with_group = get_service_cache_key(get_group_name(service_name, group_name), clusters)
        service_info, exist = self.service_info_cache.service_info_map.get(service_name_with_group)

        if not is_subscribed or not exist:
            service_info = self.grpc_client_proxy.subscribe(service_name, group_name, clusters)
            if service_info is None:
                raise NacosException(ErrorCode.SERVER_ERROR, 'failed to subscribe')
        service = service_info
        self.service_info_cache.process_service(service_info)
        return service

    def unsubscribe(self, service_name, group_name, clusters):
        self.service_info_holder.stop_update_if_contain(get_group_name(service_name, group_name), clusters)
        return self.grpc_client_proxy.unsubscribe(service_name, group_name, clusters)

    def close_client(self):
        self.grpc_client_proxy.close_client()

    def __get_execute_client_proxy(self, instance: Instance) -> NamingClientProxy:
        return self.grpc_client_proxy if instance.is_ephemeral() else self.http_client_proxy

    def shutdown(self) -> None:
        self.logger.info("%s do shutdown begin" % self.__class__.__name__)
        self.service_info_update_service.shutdown()
        self.http_client_proxy.shutdown()
        self.grpc_client_proxy.shutdown()
        self.executor.shutdown()
        self.logger.info("%s do shutdown stop" % self.__class__.__name__)
