import json
import logging
import threading
from typing import Dict

from v2.nacos.common.constants import Constants
from v2.nacos.common.client_config import ClientConfig
from v2.nacos.transport.nacos_server_connector import NacosServerConnector


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
        self.task: threading.Timer = None  # 保存心跳任务的引用


class HeartbeatReactor:
    def __init__(self, client_config: ClientConfig, nacos_server_connector: NacosServerConnector):
        self.beat_info_map: Dict[str, HeartbeatInfo] = {}
        self.logger = logging.getLogger(Constants.NAMING_MODULE)
        self.nacos_server_connector = nacos_server_connector
        self.client_config = client_config
        self.lock = threading.Lock()

    def _send_heartbeat(self, beat_info: HeartbeatInfo):
        self.logger.info("[auto-beat-task] beat task start, ip:%s, port:%s, service_name:%s, group_name:%s",
                         beat_info.ip, beat_info.port, beat_info.service_name, beat_info.group_name)
        try:
            beat_data = {
                "serviceName": beat_info.service_name,
                "ip": beat_info.ip,
                "port": beat_info.port,
                "weight": beat_info.weight,
                "ephemeral": True

            }

            if beat_info.cluster_name is not None:
                beat_data["cluster"] = beat_info.cluster_name

            if beat_info.metadata is not None:
                if isinstance(beat_info.metadata, str):
                    beat_data["metadata"] = json.loads(beat_info.metadata)
                else:
                    beat_data["metadata"] = beat_info.metadata

            params = {
                "serviceName": beat_info.service_name,
                "beat": json.dumps(beat_data),
                "groupName": beat_info.group_name
            }

            if self.client_config.namespace_id:
                params["namespaceId"] = self.client_config.namespace_id

            url = Constants.SERVICE_BASE_PATH + "/instance/beat"

            self.nacos_server_connector.req_api(url, None, beat_data, None, "PUT")

            self.logger.info("[auto-beat-task] ip:%s, port:%s, service_name:%s, namespace:%s",
                             beat_info.ip, beat_info.port, beat_info.service_name, self.client_config.namespace_id)

        except Exception as e:
            self.logger.error(
                "[auto-beat-task] failed to send heartbeat for ip:%s, port:%s, service_name:%s, namespace:%s, exception: %s",
                beat_info.ip, beat_info.port, beat_info.service_name, self.client_config.namespace_id, str(e))
        self._schedule_heartbeat(beat_info)

    def _schedule_heartbeat(self, beat_info: HeartbeatInfo):
        timer = threading.Timer(beat_info.heartbeat_interval, self._send_heartbeat, args=[beat_info])
        beat_info.task = timer
        timer.start()

    def add_beat_info(self, service_name, beat_info: HeartbeatInfo):
        beat_info_key = "%s#%s#%s" % (service_name, beat_info.ip, beat_info.port)
        with self.lock:
            exist_beat_info = self.beat_info_map.get(beat_info_key)
            if exist_beat_info and exist_beat_info.task:
                exist_beat_info.task.cancel()

            self.beat_info_map[beat_info_key] = beat_info
            self.schedule_heartbeat(beat_info)

    def remove_beat_info(self, service_name, ip, port):
        beat_info_key = f"{service_name}#{ip}#{port}"
        with self.lock:
            exist_beat_info = self.beat_info_map.pop(beat_info_key, None)
            if exist_beat_info and exist_beat_info.task:
                exist_beat_info.task.cancel()  # 取消心跳任务

    def stop_all_beats(self):
        with self.lock:
            for beat_info in self.beat_info_map.values():
                if beat_info.task:
                    beat_info.task.cancel()  # 取消每一个心跳任务
            self.beat_info_map.clear()  # 清空心跳信息映射
