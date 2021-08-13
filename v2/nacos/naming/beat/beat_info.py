class BeatInfo:
    def __init__(self, port=None,
                 ip=None,
                 weight=None,
                 service_name=None,
                 cluster=None,
                 metadata=None,
                 scheduled=None,
                 period=None,
                 stopped=None):
        self.port = port
        self.ip = ip
        self.weight = weight
        self.service_name = service_name
        self.cluster = cluster
        self.metadata = metadata
        self.scheduled = scheduled
        self.period = period
        self.stopped = stopped

    def is_scheduled(self):
        return self.scheduled

    def is_stop(self):
        return self.stopped

    def __str__(self):
        return "BeatInfo{port=" + self.port + ", ip='" + self.ip + "', weight=" + self.weight + ", serviceName='" + \
            self.service_name + "', cluster='" + self.cluster + "', metadata=" + self.metadata + ", scheduled=" + \
            self.scheduled + ", period=" + self.period + ", stopped=" + self.stopped + "}"
