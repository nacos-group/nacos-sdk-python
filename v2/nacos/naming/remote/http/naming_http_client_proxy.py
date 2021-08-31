import logging


class NamingHttpClientProxy:
    DEFAULT_SERVER_PORT = 8848

    def __init__(self, logger, namespace_id=None,
                 security_proxy=None,
                 server_list_manager=None,
                 properties=None,
                 service_info_holder=None):
        # logging.basicConfig()
        # self.logger = logging.getLogger(__name__)
        self.logger = logger

        self.server_list_manager = server_list_manager
        self.server_port = NamingHttpClientProxy.DEFAULT_SERVER_PORT
        self.namespace_id = namespace_id

