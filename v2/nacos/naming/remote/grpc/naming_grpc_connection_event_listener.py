from v2.nacos.naming.dtos.instance import Instance
from v2.nacos.naming.remote.grpc.naming_grpc_client_proxy import NamingGrpcClientProxy
from v2.nacos.remote.iconnection_event_listener import ConnectionEventListener


class NamingGrpcConnectionEventListener(ConnectionEventListener):
    def __init__(self, client_proxy: NamingGrpcClientProxy):
        self.client_proxy = client_proxy
        self.registered_instance_cached = {}
        self.subscribe = []

    def on_connected(self) -> None:
        pass

    def on_disconnect(self) -> None:
        pass

    def __redo_subscribe(self) -> None:
        pass

    def __redo_register_each_service(self) -> None:
        pass

    def __redo_register_each_instance(self, server_name: str, group_name: str, instance: Instance) -> None:
        pass

    def cache_instance_for_redo(self, service_name: str, group_name: str, instance: Instance) -> None:
        pass

    def remove_instance_for_redo(self, service_name: str, group_name: str, instance: Instance) -> None:
        pass

    def cache_subscribe_for_redo(self, full_service_name: str, cluster: str) -> None:
        pass

    def remove_subscriber_for_redo(self, full_service_name: str, cluster: str) -> None:
        pass
