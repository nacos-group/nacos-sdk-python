import logging

from v2.nacos.naming.nacos_naming_service import NacosNamingService
import sys

SERVER_ADDRESSES = "http://mse-96d50180-p.nacos-ans.mse.aliyuncs.com:8848"
NAMESPACE = "test"

if __name__ == '__main__':
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

    naming = NacosNamingService(logger, properties)
    # naming.register_instance("nacos.test.3", "default", "11.11.11.11", 8888, "default")
    # print("step:2")
