import logging
import sched
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

from v2.nacos.naming.core.server_list_manager import ServerListManager
from v2.nacos.naming.core.service_info_update_service import ServiceInfoUpdateService
from v2.nacos.naming.dtos.instance import Instance
from v2.nacos.naming.remote.grpc.naming_grpc_client_proxy import NamingGrpcClientProxy
from v2.nacos.naming.remote.http.naming_http_client_proxy import NamingHttpClientProxy
from v2.nacos.naming.remote.inaming_client_proxy import NamingClientProxy
from v2.nacos.security.security_proxy import SecurityProxy


class NamingClientProxyDelegate(NamingClientProxy):
    def __init__(self, namespace, service_info_holder, properties, change_notifier):
        logging.basicConfig()
        self.logger = logging.getLogger(__name__)

        self.security_info_refresh_interval_second = 5
        self.service_info_update_service = ServiceInfoUpdateService(properties, service_info_holder,
                                                                    self, change_notifier)
        self.server_list_manager = ServerListManager(properties)
        self.server_info_list = service_info_holder
        self.security_proxy = SecurityProxy(properties)
        self.__init_security_proxy()
        self.http_client_proxy = NamingHttpClientProxy(namespace, self.security_proxy,
                                                       self.server_list_manager, properties, service_info_holder)
        self.grpc_client_proxy = NamingGrpcClientProxy(namespace, self.security_proxy, self.server_list_manager,
                                                       properties, service_info_holder)

    def __init_security_proxy(self):
        self.login_timer = sched.scheduler(time.time, time.sleep)
        self.login_timer.enter(self.security_info_refresh_interval_second, 0, self.security_proxy.login,
                               (self.server_list_manager.get_server_list(),))
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.executor.submit(self.login_timer.run)

    def register_service(self, service_name: str, group_name: str, instance: Instance) -> None:
        self.__get_execute_client_proxy(instance).register_service(service_name, group_name, instance)

    def deregister_service(self, service_name, group_name, instance) -> None:
        self.__get_execute_client_proxy(instance).deregister_service(service_name, group_name, instance)

    def update_instance(self, service_name, group_name, instance):
        pass

    def query_instances_of_service(self, service_name, group_name, clusters, udp_port, healthy_only):
        pass

    def query_service(self, service_name, group_name):
        pass

    def create_service(self, service, selector):
        pass

    def delete_service(self, service_name, group_name):
        pass

    def update_service(self, service, selector):
        pass

    def get_service_list(self, page_no, page_size, group_name, selector):
        pass

    def subscribe(self, service_name, group_name, clusters):
        pass

    def unsubscribe(self, modified_instances):
        pass

    def server_healthy(self):
        pass

    def __get_execute_client_proxy(self, instance: Instance) -> NamingClientProxy:
        return self.grpc_client_proxy if instance.is_ephemeral() else self.http_client_proxy

    def shutdown(self) -> None:
        self.logger.info("%s do shutdown begin" % self.__class__.__name__)
        self.service_info_update_service.shutdown()
        self.http_client_proxy.shutdown()
        self.grpc_client_proxy.shutdown()
        self.executor.shutdown()
        self.logger.info("%s do shutdown stop" % self.__class__.__name__)
