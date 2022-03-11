import logging
import time

from v2.nacos.config.ilistener import Listener
from v2.nacos.config.nacos_config_service import NacosConfigService

SERVER_ADDRESSES = "http://127.0.0.1:8848"
NAMESPACE = ""
DATA_ID1 = "nacos_config_test1"
DATA_ID2 = "nacos_config_test2"
GROUP = "default"
CONFIG_CONTENT = "content"
CONFIG_TYPE = "text"
TIMEOUT = 3000

properties = {
        "namespace": NAMESPACE,
        "serverAddr": SERVER_ADDRESSES,
        "username": "nacos",
        "password": "nacos",
        "endpoint": "",
        "contextPath": "/nacos",
        "ak": "nnn",
        "sk": "nnn"
    }

logger = logging.getLogger("nacos")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s:%(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logger.removeHandler(handler)


class DemoListener(Listener):
    def get_executor(self):
        return

    def receive_config_info(self, config_info: str):
        print("receive_config_info:", config_info)


if __name__ == '__main__':
    config = NacosConfigService(logger, properties)
    time.sleep(1)

    # get server status
    server_status = config.get_server_status()
    print("server_status:", server_status)

    # publish config
    publish_config = config.publish_config(DATA_ID1, GROUP, CONFIG_CONTENT, CONFIG_TYPE)
    print("publish_config:", str(publish_config))
    time.sleep(1)

    # publish config cas
    publish_config_cas = config.publish_config_cas(DATA_ID2, GROUP, CONFIG_CONTENT, "", CONFIG_TYPE)
    print("publish_config_cas:", str(publish_config_cas))
    time.sleep(1)

    # get config
    config_content = config.get_config(DATA_ID1, GROUP, TIMEOUT)
    print("get_config:", config_content)

    # add listener
    demo_listener = DemoListener()
    config.add_listener(DATA_ID1, GROUP, demo_listener)
    print("add_listener complete")
    time.sleep(1)

    # remove listener
    config.remove_listener(DATA_ID1, GROUP, demo_listener)
    print("remove_listener complete")
    time.sleep(1)

    # get config and sign listener
    config_content_2 = config.get_config_and_sign_listener(DATA_ID1, GROUP, TIMEOUT, demo_listener)
    print("get_config_and_sign_listener:", config_content_2)
    time.sleep(1)

    # remove config
    remove_config = config.remove_config(DATA_ID1, GROUP)
    print("remove_config:", str(remove_config))
    time.sleep(1)

    # shutdown
    time.sleep(5)
    config.shutdown()
    print("shutdown")
