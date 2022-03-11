import logging
import time

from v2.nacos.naming.dtos.instance import Instance
from v2.nacos.naming.dtos.service import Service
from v2.nacos.naming.ievent_listener import EventListener
from v2.nacos.naming.nacos_naming_service import NacosNamingService

SERVER_ADDRESSES = "http://127.0.0.1:8848"
NAMESPACE = "public"

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


class DemoListener(EventListener):

    def on_event(self, event) -> None:
        print("on event!")


if __name__ == '__main__':
    naming = NacosNamingService(logger, properties)

    # register instance
    service_meta = {"test": True}
    service = Service(
        name="nacos.test.1", groupName="TEST", appName="nacos-naming", protectThreadhold=0.8, metadata=service_meta
    )

    instance_meta = {"site": "test"}
    instance = Instance(ip="11.11.11.11", port=8888, weight=2.0, service=service, metadata=instance_meta)

    naming.register_instance("nacos.test.2", "default", instance)
    time.sleep(1)
    # get all instances
    all_instances = naming.get_all_instances("nacos.test.2", "default", ["DEFAULT"], True)
    print(all_instances)

    # get services of server
    list_view = naming.get_services_of_server(0, 1024, "default", None)
    print("list_view:", str(list_view))

    # subscribe
    demo_listener = DemoListener()
    naming.subscribe("nacos.test.2", "default", [], demo_listener)

    # select one healthy instance
    one_healthy_instance = naming.select_one_healthy_instance("nacos.test.2", "default", [], True)
    print("select one healthy instance:", str(one_healthy_instance))

    # get server status
    server_status = naming.get_server_status()
    time.sleep(1)
    print("server_status:", server_status)

    # unsubscribe
    naming.unsubscribe("nacos.test.2", "default", [], demo_listener)
    time.sleep(1)
    print("unsubscribed!")

    # deregister instance
    naming.deregister_instance("nacos.test.2", "default", "11.11.11.11", 8888, "DEFAULT")
    time.sleep(1)
    print("deregister instance!")

    # shutdown
    naming.shutdown()
    print("shutdown")