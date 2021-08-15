class Service:
    def __init__(self, name=None, protect_threshold=0, app_name=None, group_name=None, metadata=None):
        if metadata is None:
            metadata = {}
        self.name = name
        self.protect_threshold = protect_threshold
        self.app_name = app_name
        self.group_name = group_name
        self.metadata = metadata

    def __str__(self):
        return "Service{name='" + self.name + "', protectThreshold=" + self.protect_threshold + ", appName='" + \
            self.app_name + "', groupName='" + self.group_name + "', metadata=" + self.metadata + "}"
