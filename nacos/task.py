import threading
import logging
import time


class HeartbeatInfo:
    def __init__(self,
                 service_name,
                 ip,
                 port,
                 cluster_name,
                 group_name,
                 weight,
                 heartbeat_interval,
                 metadata,
                 ):
        self.service_name = service_name
        self.ip = ip
        self.port = port
        self.cluster_name = cluster_name
        self.group_name = group_name
        self.weight = weight
        self.metadata = metadata
        self.heartbeat_interval = heartbeat_interval


class HeartbeatTask(threading.Thread):
    def __init__(self,
                 beat_info: HeartbeatInfo,
                 client,
                 ):
        self.logger = logging.getLogger('nacos.client')
        super().__init__()
        self.beat_info = beat_info
        self.client = client
        self.daemon = True
        self.stopped = False

    def run(self):
        self.logger.info("[auto-beat-task] beat task start, ip:%s, port:%s, service_name:%s, group_name:%s" % (
            self.beat_info.ip, self.beat_info.port, self.beat_info.service_name, self.beat_info.group_name))
        while not self.stopped:
            try:
                self.client.send_heartbeat(self.beat_info.service_name,
                                           self.beat_info.ip,
                                           self.beat_info.port,
                                           self.beat_info.cluster_name,
                                           self.beat_info.weight,
                                           self.beat_info.metadata,
                                           True,
                                           self.beat_info.group_name)
                time.sleep(self.beat_info.heartbeat_interval)
            except Exception as e:
                self.logger.error("[auto-beat-task] beat task error: %s" % e)
                time.sleep(self.beat_info.heartbeat_interval)
        self.logger.info("[auto-beat-task] beat task stopped, ip:%s, port:%s, service_name:%s, group_name:%s" % (
            self.beat_info.ip, self.beat_info.port, self.beat_info.service_name, self.beat_info.group_name))

    def stop(self):
        self.stopped = True
