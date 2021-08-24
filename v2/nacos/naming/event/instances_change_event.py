from v2.nacos.naming.utils.ievent import Event


class InstancesChangeEvent(Event):
    def __init__(self, service_name: str, group_name: str, clusters: str, hosts: list):
        self.service_name = service_name
        self.group_name = group_name
        self.clusters = clusters
        self.hosts = hosts

    def get_service_name(self) -> str:
        return self.service_name

    def get_group_name(self) -> str:
        return self.group_name

    def get_clusters(self) -> str:
        return self.clusters

    def get_hosts(self) -> list:
        return self.hosts
