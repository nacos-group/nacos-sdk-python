import json
import logging
import uuid


from v2.nacos.common.constants import Constants
from v2.nacos.common.utils import get_current_time_millis
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.naming.cache.service_info_holder import ServiceInfoHolder
from v2.nacos.naming.dtos.abstract_selector import AbstractSelector
from v2.nacos.naming.dtos.instance import Instance
from v2.nacos.naming.dtos.service_info import ServiceInfo
from v2.nacos.naming.utils.naming_remote_constants import NamingRemoteConstants
from v2.nacos.naming.remote.grpc.naming_grpc_connection_event_listener import NamingGrpcConnectionEventListener
from v2.nacos.naming.remote.grpc.naming_push_request_handler import NamingPushRequestHandler
from v2.nacos.naming.remote.inaming_client_proxy import NamingClientProxy
from v2.nacos.naming.utils.common_params import CommonParams
from v2.nacos.naming.utils.naming_utils import NamingUtils
from v2.nacos.remote.iserver_list_factory import ServerListFactory
from v2.nacos.remote.list_view import ListView
from v2.nacos.remote.remote_constants import RemoteConstants
from v2.nacos.remote.requests.abstract_naming_request import AbstractNamingRequest
from v2.nacos.remote.requests.instance_request import InstanceRequest
from v2.nacos.remote.requests.service_list_request import ServiceListRequest
from v2.nacos.remote.requests.service_query_request import ServiceQueryRequest
from v2.nacos.remote.requests.subscribe_service_request import SubscribeServiceRequest
from v2.nacos.remote.responses.query_service_response import QueryServiceResponse
from v2.nacos.remote.responses.response import Response
from v2.nacos.remote.responses.service_list_response import ServiceListResponse
from v2.nacos.remote.responses.subscribe_service_response import SubscribeServiceResponse
from v2.nacos.remote.rpc_client_factory import RpcClientFactory
from v2.nacos.remote.utils import ConnectionType, response_code
from v2.nacos.security.security_proxy import SecurityProxy
from v2.nacos.utils.app_name_utils import AppNameUtils
from v2.nacos.utils.sign_util import SignUtil


class NamingGrpcClientProxy(NamingClientProxy):
    APP_FILED = "app"

    SIGNATURE_FILED = "signature"

    DATA_FILED = "data"

    AK_FILED = "ak"

    SEPARATOR = "@@"

    def __init__(self, logger, namespace: str, security_proxy: SecurityProxy, server_list_factory: ServerListFactory,
                 properties: dict, service_info_holder: ServiceInfoHolder):
        self.logger = logger

        self.namespace = namespace
        self.uuid = uuid.uuid4()
        self.security_proxy = security_proxy
        self.properties = properties
        if CommonParams.NAMING_REQUEST_TIMEOUT in properties.keys():
            request_timeout = properties[CommonParams.NAMING_REQUEST_TIMEOUT]
        else:
            request_timeout = -1
        self.request_timeout = request_timeout
        labels = {RemoteConstants.LABEL_SOURCE: RemoteConstants.LABEL_SOURCE_SDK,
                  RemoteConstants.LABEL_MODULE: RemoteConstants.LABEL_MODULE_NAMING}
        self.rpc_client = RpcClientFactory(self.logger).create_client(str(self.uuid), ConnectionType.GRPC, labels)
        self.naming_grpc_connection_event_listener = NamingGrpcConnectionEventListener(self.logger, self)
        self.__start(server_list_factory, service_info_holder)

    def __start(self, server_list_factory: ServerListFactory, service_info_holder: ServiceInfoHolder):
        self.rpc_client.set_server_list_factory(server_list_factory)
        self.rpc_client.start()
        self.rpc_client.register_server_request_handler(NamingPushRequestHandler(service_info_holder))
        self.rpc_client.register_connection_listener(self.naming_grpc_connection_event_listener)

    def __request_to_server(self, request: AbstractNamingRequest, response_class):
        try:
            request.put_all_header(self._get_security_headers())
            request.put_all_header(self._get_spas_headers(
                NamingUtils.get_grouped_name_optional(request.get_service_name(), request.get_group_name()))
            )
            response = self.rpc_client.request(request) if self.request_timeout < 0 else \
                self.rpc_client.request(request, self.request_timeout)

            if response.get_result_code() != response_code["success"]:
                raise NacosException(str(response.get_error_code()) + response.get_message())
            if issubclass(response.__class__, response_class):  # todo check and fix if anything wrong
                return response
            self.logger.error("Server return unexpected response '%s', expected response should be '%s'"
                              % (response.__class__.__name__, response_class.__name__))
        except NacosException as e:
            raise NacosException(str(NacosException.SERVER_ERROR) + " Request nacos server failed: " + str(e))

        raise NacosException(str(NacosException.SERVER_ERROR) + " Server return invalid response")

    def _get_security_headers(self) -> dict:
        result = {}
        if self.security_proxy.get_access_token().strip():
            result[Constants.ACCESS_TOKEN] = self.security_proxy.get_access_token()
        return result

    def _get_spas_headers(self, service_name: str) -> dict:
        result = {}
        ak = self.__get_access_key()
        sk = self.__get_secret_key()
        result[NamingGrpcClientProxy.APP_FILED] = AppNameUtils.get_app_name()
        if ak.strip() and sk.strip():
            try:
                sign_data = self.__get_sign_data(service_name)
                signature = SignUtil.sign(sign_data, sk)
                result[NamingGrpcClientProxy.SIGNATURE_FILED] = signature
                result[NamingGrpcClientProxy.DATA_FILED] = sign_data
                result[NamingGrpcClientProxy.AK_FILED] = ak
            except NacosException as e:
                self.logger.error("Inject ak/sk failed.", e)
        return result

    def __get_access_key(self) -> str:
        return self.properties["ak"]

    def __get_secret_key(self) -> str:
        return self.properties["sk"]

    @staticmethod
    def __get_sign_data(service_name: str) -> str:
        return str(get_current_time_millis()) + NamingGrpcClientProxy.SEPARATOR + service_name if service_name.strip() else \
            str(get_current_time_millis())

    def register_service(self, service_name, group_name, instance):
        self.logger.info("[REGISTER-SERVICE] %s registering service %s with instance %s" %
                         (self.namespace, service_name, instance))
        request = InstanceRequest(namespace=self.namespace, serviceName=service_name, groupName=group_name,
                                  type=NamingRemoteConstants.REGISTER_INSTANCE, instance=instance)
        self.__request_to_server(request, Response)

    def deregister_service(self, service_name, group_name, instance):
        self.logger.info("[DEREGISTER-SERVICE] %s deregistering service %s with instance: %s"
                         % (self.namespace, service_name, instance))
        self.naming_grpc_connection_event_listener.remove_instance_for_redo(service_name, group_name, instance)
        request = InstanceRequest(namespace=self.namespace, serviceName=service_name, groupName=group_name,
                                  type=NamingRemoteConstants.DE_REGISTER_INSTANCE, instnace=instance)
        self.__request_to_server(request, Response)

    def update_instance(self, service_name, group_name, instance):
        pass

    def query_instances_of_service(self, service_name, group_name, clusters, udp_port, healthy_only):
        request = ServiceQueryRequest(
            namespace=self.namespace, serviceName=service_name, groupName=group_name, clusters=clusters,
            healthyOnly=healthy_only, udpPort=udp_port
        )
        response = self.__request_to_server(request, QueryServiceResponse)
        if isinstance(response, QueryServiceResponse):
            service_info_dict = response.get_service_info()
            service_info = ServiceInfo.build(service_info_dict)

            response.serviceInfo = service_info
            return response.get_service_info()
        else:
            self.logger.error("[QUERY-INSTANCE-OF-SERVICE] unexpected type of response: %s"
                              % response.__class__.__name__)
            raise NacosException("Unexpected type of response!")

    def query_service(self, service_name, group_name):
        pass

    def create_service(self, service, selector):
        pass

    def delete_service(self, service_name, group_name):
        pass

    def update_service(self, service, selector):
        pass

    def get_service_list(self, page_no, page_size, group_name, selector: AbstractSelector):
        if selector and selector.get_type() == "label":
            selector_str = json.dumps(selector)
        else:
            selector_str = None

        request = ServiceListRequest(
            namespace=self.namespace, serviceName="", groupName=group_name, pageNo=page_no, pageSize=page_size, selector=selector_str)
        response = self.__request_to_server(request, ServiceListResponse)
        if isinstance(response, ServiceListResponse):
            result = ListView(response.get_service_names(), response.get_count())
            return result
        else:
            self.logger.error("[GET-SERVICE-RESPONSE] unexpected type of response: %s"
                              % response.__class__.__name__)
            raise NacosException("Unexpected type of response!")

    def subscribe(self, service_name: str, group_name: str, clusters: str):
        request = SubscribeServiceRequest(
            namespace=self.namespace, groupName=group_name, serviceName=service_name, clusters=clusters, subscribe=True)
        response = self.__request_to_server(request, SubscribeServiceResponse)
        self.naming_grpc_connection_event_listener.cache_subscribe_for_redo(
            NamingUtils.get_grouped_name(service_name, group_name), clusters
        )
        if isinstance(response, SubscribeServiceResponse):
            service_info_dict = response.get_service_info()
            service_info = ServiceInfo.build(service_info_dict)  # covert dict to ServiceInfo
            response.serviceInfo = service_info
            return response.get_service_info()
        else:
            self.logger.error("[SUBSCRIBE] unexpected type of response: %s"
                              % response.__class__.__name__)
            raise NacosException("Unexpected type of response!")

    def unsubscribe(self, service_name: str, group_name: str, clusters: str) -> None:
        request = SubscribeServiceRequest(
            namespace=self.namespace, serviceName=service_name, groupName=group_name, clusters=clusters, subscribe=False
        )
        self.__request_to_server(request, SubscribeServiceResponse)
        self.naming_grpc_connection_event_listener.remove_subscriber_for_redo(
            NamingUtils.get_grouped_name(service_name, group_name), clusters
        )

    def update_beat_info(self, modified_instances: list) -> None:
        pass

    def server_healthy(self) -> bool:
        return self.rpc_client.is_running()

    def shutdown(self) -> None:
        self.rpc_client.shutdown()

    def is_enable(self) -> bool:
        return self.rpc_client.is_running()
