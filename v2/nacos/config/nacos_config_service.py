import logging

from v2.nacos.config.ilistener import Listener
from v2.nacos.property_key_constants import PropertyKeyConstants


class NacosConfigService:
    UP = "UP"

    DOWN = "DOWN"

    def __init__(self, properties: dict):
        logging.basicConfig()
        self.logger = logging.getLogger(__name__)

        # todo
        self.namespace = properties[PropertyKeyConstants.NAMESPACE]
        self.worker = ClientWorker()

    def get_config(self, data_id: str, group: str, timeout_ms: int) -> str:
        pass

    def get_config_and_sign_listener(self, data_id: str, group: str, timeout_ms: int, listener: Listener) -> str:
        pass

    def add_listener(self, data_id: str, group: str, listener: Listener) -> None:
        pass

    def publish_config(self, data_id: str, group: str, content: str, config_type: str) -> bool:
        pass

    def publish_config_cas(self, data_id: str, group: str, content: str, cas_md5: str, config_type: str) -> bool:
        pass

    def remove_config(self, data_id: str, group: str) -> bool:
        pass

    def remove_listener(self, data_id: str, group: str, listener: Listener) -> None:
        pass

    def get_server_status(self) -> str:
        pass

    def shutdown(self) -> None:
        pass