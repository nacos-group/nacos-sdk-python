import logging

from v2.nacos.naming.model.instance import Instance
from v2.nacos.naming.remote.naming_client_proxy import NamingClientProxy


class NamingHttpClientProxy(NamingClientProxy):
    DEFAULT_SERVER_PORT = 8848

    def __init__(self, namespace_id=None,
                 security_proxy=None,
                 server_list_manager=None,
                 properties=None,
                 service_info_holder=None):
        logging.basicConfig()
        self.logger = logging.getLogger(__name__)

        self.server_list_manager = server_list_manager
        self.server_port = NamingHttpClientProxy.DEFAULT_SERVER_PORT
        self.namespace_id = namespace_id

    def register_instance(self, service_name: str, group_name: str, instance: Instance) -> bool:
        return True
