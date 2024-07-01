import json
import logging
from http import HTTPStatus
from urllib.error import HTTPError

from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, NO_RIGHT, SERVER_ERROR
from v2.nacos.common.preserved_metadata_key import PreservedMetadataKeys
from v2.nacos.common.client_config import ClientConfig
from v2.nacos.naming.cache.service_info_cache import ServiceInfoCache
from v2.nacos.naming.model.instance import Instance
from v2.nacos.naming.remote.http.heart_beat_reactor import HeartbeatReactor, HeartbeatInfo
from v2.nacos.naming.remote.naming_client_proxy import NamingClientProxy
from v2.nacos.transport.nacos_server_connector import NacosServerConnector


class NamingHttpClientProxy(NamingClientProxy):
    DEFAULT_SERVER_PORT = 8848

    def __init__(self,
                 client_config: ClientConfig,
                 nacos_server_connector: NacosServerConnector,
                 service_info_cache=ServiceInfoCache):
        self.logger = logging.getLogger(Constants.NAMING_MODULE)
        self.client_config = client_config
        self.nacos_server_connector = nacos_server_connector
        self.service_info_cache = service_info_cache

        self.server_port = NamingHttpClientProxy.DEFAULT_SERVER_PORT
        self.namespace_id = client_config.namespace_id
        self.heartbeatReactor = HeartbeatReactor(client_config, nacos_server_connector)

    def register_instance(self, service_name: str, group_name: str, instance: Instance) -> bool:
        self.logger.info("[register_instance] ip:%s, port:%s, service_name:%s, namespace:%s" % (
            instance.ip, instance.port, service_name, self.namespace_id))

        params = {
            "ip": instance.ip,
            "port": instance.port,
            "serviceName": service_name,
            "weight": instance.weight,
            "enable": instance.enable,
            "healthy": instance.healthy,
            "clusterName": instance.cluster_name,
            "ephemeral": instance.ephemeral,
            "groupName": group_name,
            "app": self.client_config.app_name,
        }

        if self.namespace_id:
            params["namespaceId"] = self.namespace_id

        params["metadata"] = json.dumps(instance.metadata)
        try:
            resp = self.nacos_server_connector.req_api("/nacos/v1/ns/instance", None, None, params, "POST")
            c = resp.read()
            self.logger.info(
                "[add-naming-instance] ip:%s, port:%s, service_name:%s, namespace:%s, server response:%s" % (
                    instance.ip, instance.port, service_name, self.namespace_id, c))
            res = c == b"ok"

            if res and instance.ephemeral:
                heartbeat_interval = Constants.DEFAULT_HEARTBEAT_INTERVAL if instance.metadata is None else instance.metadata.get(
                    PreservedMetadataKeys.HEART_BEAT_INTERVAL, Constants.DEFAULT_HEARTBEAT_INTERVAL)
                beat_info = HeartbeatInfo(service_name,
                                          instance.ip,
                                          instance.port,
                                          instance.cluster_name,
                                          group_name,
                                          instance.weight,
                                          heartbeat_interval,
                                          instance.metadata
                                          )
                self.heartbeatReactor.add_beat_info(service_name, beat_info)
            return res
        except HTTPError as e:
            if e.code == HTTPStatus.FORBIDDEN:
                raise NacosException(NO_RIGHT, "Insufficient privilege.")
            else:
                raise NacosException(SERVER_ERROR, "Request Error, code is %s" % e.code)
        except Exception as e:
            self.logger.exception("[add-naming-instance] exception %s occur" % str(e))
            raise
