import logging
import sched
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

from v2.nacos.naming.core.server_list_manager import ServerListManager
from v2.nacos.naming.core.service_info_update_service import ServiceInfoUpdateService
from v2.nacos.naming.dtos.abstract_selector import AbstractSelector
from v2.nacos.naming.dtos.instance import Instance
from v2.nacos.naming.dtos.service import Service
from v2.nacos.naming.dtos.service_info import ServiceInfo
from v2.nacos.naming.remote.grpc.naming_grpc_client_proxy import NamingGrpcClientProxy
from v2.nacos.naming.remote.http.naming_http_client_proxy import NamingHttpClientProxy
from v2.nacos.naming.remote.inaming_client_proxy import NamingClientProxy
from v2.nacos.naming.utils.naming_utils import NamingUtils
from v2.nacos.remote.list_view import ListView
from v2.nacos.security.security_proxy import SecurityProxy


class NamingClientProxyDelegate(NamingClientProxy):
    def __init__(self, namespace, service_info_holder, properties, change_notifier):
        logging.basicConfig()
        self.logger = logging.getLogger(__name__)

        self.security_info_refresh_interval_second = 5
        self.service_info_update_service = ServiceInfoUpdateService(properties, service_info_holder,
                                                                    self, change_notifier)
        self.server_list_manager = ServerListManager(properties)
        self.server_info_holder = service_info_holder
        self.security_proxy = SecurityProxy(properties)
        self.__init_security_proxy()
        self.http_client_proxy = NamingHttpClientProxy(namespace, self.security_proxy,
                                                       self.server_list_manager, properties, service_info_holder)
        self.grpc_client_proxy = NamingGrpcClientProxy(namespace, self.security_proxy, self.server_list_manager,
                                                       properties, service_info_holder)

    def __init_security_proxy(self):
        self.login_timer = sched.scheduler(time.time, time.sleep)
        self.login_timer.enter(self.security_info_refresh_interval_second, 0, self.security_proxy.login_servers,
                               (self.server_list_manager.get_server_list(),))
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.executor.submit(self.login_timer.run)

    def register_service(self, service_name: str, group_name: str, instance: Instance) -> None:
        self.__get_execute_client_proxy(instance).register_service(service_name, group_name, instance)

    def deregister_service(self, service_name: str, group_name: str, instance: Instance) -> None:
        self.__get_execute_client_proxy(instance).deregister_service(service_name, group_name, instance)

    def update_instance(self, service_name: str, group_name: str, instance: Instance) -> None:
        pass

    def query_instances_of_service(self, service_name: str, group_name: str, clusters: str,
                                   udp_port: int, healthy_only: bool):
        return self.grpc_client_proxy.query_instances_of_service(
            service_name, group_name, clusters, udp_port, healthy_only
        )

    def query_service(self, service_name: str, group_name: str) -> Service:
        pass

    def create_service(self, service: Service, selector: AbstractSelector) -> None:
        pass

    def delete_service(self, service_name: str, group_name: str) -> bool:
        pass

    def update_service(self, service: Service, selector: AbstractSelector) -> None:
        pass

    def get_service_list(self, page_no: int, page_size: int, group_name: str, selector: AbstractSelector) -> ListView:
        return self.grpc_client_proxy.get_service_list(
            page_no, page_size, group_name, selector
        )

    def subscribe(self, service_name: str, group_name: str, clusters: str) -> ServiceInfo:
        service_name_with_group = NamingUtils.get_grouped_name(service_name, group_name)
        service_key = ServiceInfo.get_key(service_name_with_group, clusters)
        if service_key in self.server_info_holder.get_service_info_map().keys():
            result = self.grpc_client_proxy.subscribe(service_name, group_name, clusters)
        else:
            result = self.server_info_holder.get_service_info_map()[service_key]

        self.service_info_update_service.schedule_update_if_absent(service_name, clusters)
        self.server_info_holder.process_service_info(result)
        return result

    def unsubscribe(self, service_name: str, group_name: str, clusters: str) -> None:
        self.service_info_update_service.stop_update_if_contain(service_name, group_name, clusters)
        self.grpc_client_proxy.unsubscribe(service_name, group_name, clusters)

    def update_beat_info(self, modified_instances: list) -> None:
        pass

    def server_healthy(self) -> bool:
        self.grpc_client_proxy.server_healthy()

    def __get_execute_client_proxy(self, instance: Instance) -> NamingClientProxy:
        return self.grpc_client_proxy if instance.is_ephemeral() else self.http_client_proxy

    def shutdown(self) -> None:
        self.logger.info("%s do shutdown begin" % self.__class__.__name__)
        self.service_info_update_service.shutdown()
        self.http_client_proxy.shutdown()
        self.grpc_client_proxy.shutdown()
        self.executor.shutdown()
        self.logger.info("%s do shutdown stop" % self.__class__.__name__)
