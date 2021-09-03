from v2.nacos.common.lifecycle.closeable import Closeable


class ServerListManager(Closeable):
    HTTPS = "https://"

    HTTP = "http://"

    DEFAULT_NAME = "default"

    CUSTOM_NAME = "custom"

    FIXED_NAME = "fixed"

    def __init__(self, logger, properties: dict):
        self.logger = logger
        self.properties = properties

    def start(self) -> None:
        pass

    def get_server_urls(self) -> list:
        pass

    def shutdown(self) -> None:
        pass