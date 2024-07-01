class Service:
    def __init__(self, service_name, group_name, clusters, cache_only=False):
        self.service_name = service_name
        self.group_name = group_name
        self.clusters = clusters
        self.cache_only = cache_only
        self.hosts = []
