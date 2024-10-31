import logging
import uuid

from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, SERVER_ERROR, CONFLICT, CLIENT_OVER_THRESHOLD
from v2.nacos.config.cache.config_cache import ConfigCache
from v2.nacos.config.limiter import limiter
from v2.nacos.config.model.config_request import AbstractConfigRequest, ConfigQueryRequest
from v2.nacos.config.model.config_response import ConfigQueryResponse
from v2.nacos.transport.http_agent import HttpAgent
from v2.nacos.transport.nacos_server_connector import NacosServerConnector
from v2.nacos.transport.rpc_client import ConnectionType
from v2.nacos.transport.rpc_client_factory import RpcClientFactory
from v2.nacos.utils import common_util


class ConfigProxy:
    def __init__(self, client_config: ClientConfig, http_agent: HttpAgent, config_cache: ConfigCache):
        self.client_config = client_config
        self.logger = logging.getLogger(Constants.CONFIG_MODULE)
        self.rpc_client = None
        self.nacos_server_connector = NacosServerConnector(self.logger, self.client_config, http_agent)
        self.config_cache = config_cache
        self.uuid = uuid.uuid4()

    async def query_config(self, data_id: str, group: str, tenant: str, notify: bool):
        if not group:
            group = Constants.DEFAULT_GROUP

        config_query_request = ConfigQueryRequest(group=group, dataId=data_id, tenant=tenant)
        config_query_request.headers["notify"] = str(notify)

        cache_key = common_util.get_config_cache_key(data_id, group, tenant)

        if limiter.RateLimiterCheck.is_limited(cache_key):
            raise NacosException(CLIENT_OVER_THRESHOLD, "More than client-side current limit threshold")
        try:
            response = await self.request_proxy(config_query_request, ConfigQueryResponse)

            if response.is_success():
                self.config_cache.write_cache_to_disk(cache_key, response.content, response.encryptedDataKey)
                if not response.contentType:
                    response.contentType = "text"
                return response

            if response.get_error_code() == 300:
                self.config_cache.write_cache_to_disk(cache_key, "", "")
                return response

            if response.get_error_code() == 400:
                self.logger.error(
                    "[config_proxy.query_config] sub-server-error, get server config being modified concurrently, "
                    "dataId=%s, group=%s, tenant=%s", data_id, group, tenant)

                raise NacosException(CONFLICT,
                                     "data being modified, dataId:{}, group:{}, tenant:{}".format(data_id, group,
                                                                                                  tenant))

            if response.get_error_code() > 0:
                self.logger.error(
                    "[config_proxy.query_config] sub-server-error, dataId=%s, group=%s, tenant=%s, response=%s",
                    data_id, group, tenant, str(response))
                raise NacosException(response.get_error_code(),
                                     "http error, code={}, msg={}, dataId={}, group={}, tenant={}".format(
                                         response.get_error_code(), response.get_message(), data_id, group, tenant))

        except Exception as e:
            self.logger.error("[config_proxy.query_config] [unkown-error] errer: %s", str(e))
            raise

    async def request_proxy(self, request: AbstractConfigRequest, response_class):
        self.nacos_server_connector.inject_security_info(request.get_headers())
        self.nacos_server_connector.inject_config_headers_sign(request)

        try:
            response = await self.rpc_client.request(request, self.client_config.grpc_config.grpc_timeout)
            if issubclass(response.__class__, response_class):
                return response
        except Exception as e:
            raise NacosException(SERVER_ERROR, " Request nacos server failed: " + str(e))
        raise NacosException(SERVER_ERROR, " Server return invalid response")

    async def start(self):
        labels = {
            Constants.LABEL_SOURCE: Constants.LABEL_SOURCE_SDK,
            Constants.LABEL_MODULE: Constants.CONFIG_MODULE,
            Constants.APPNAME_HEADER: self.client_config.app_name
        }

        self.rpc_client = await RpcClientFactory(self.logger).create_client(
            str(self.uuid), ConnectionType.GRPC, labels,
            self.client_config, self.nacos_server_connector)

    def get_rpc_client(self):
        return self.rpc_client
