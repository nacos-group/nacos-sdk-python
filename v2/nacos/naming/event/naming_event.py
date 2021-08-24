from v2.nacos.naming.utils.ievent import Event


class NamingEvent(Event):
    def __init__(self, service_name: str, group_name: str, clusters: str, instances: list):
        self.service_name = service_name
        self.group_name = group_name
        self.clusters = clusters
        self.instances = instances
