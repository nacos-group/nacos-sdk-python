class Cluster:
    def __init__(self, service_name=None, name=None, health_checker=None, default_port=80, default_check_port=80,
                 use_ip_port_4_check=True, metadata=None):
        if metadata is None:
            metadata = []

        self.service_name = service_name
        self.name = name
        self.health_checker = health_checker
        self.default_port = default_port
        self.default_check_port = default_check_port
        self.use_ip_port_4_check = use_ip_port_4_check
        self.meta_data = metadata
