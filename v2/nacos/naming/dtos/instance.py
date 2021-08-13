import re

from v2.nacos.common.constants import Constants
from v2.nacos.common.preserved_metadata_keys import PreservedMetadataKeys


class Instance:
    def __init__(self, instance_ip=None, ip=None, port=None, weight=1.0, healthy=True, enabled=True, ephemeral=True,
                 cluster_name=None, service_name=None, metadata=None):
        if metadata is None:
            metadata = {}

        self.instance_id = instance_ip
        self.ip = ip
        self.port = port
        self.weight = weight
        self.healthy = healthy
        self.enabled = enabled
        self.ephemeral = ephemeral
        self.cluster_name = cluster_name
        self.service_name = service_name
        self.metadata = metadata

    def __str__(self):
        return "Instance{instanceId='" + self.instance_id + "', ip='" + self.ip + "', port=" + self.port + \
               ", weight=" + self.weight + ", healthy=" + self.healthy + ", enabled=" + self.enabled + \
               ", ephemeral=" + self.ephemeral + ", clusterName='" + self.cluster_name + "', serviceName='" +\
               self.service_name + "', metadata=" + self.metadata + "}"

    def to_inet_addr(self):
        return self.ip + ":" + self.port

    def is_ephemeral(self) -> bool:
        return self.ephemeral

    def get_weight(self):
        return self.weight

    def add_metadata(self, key: str, value: str) -> None:
        self.metadata[key] = value

    def get_instance_heart_beat_interval(self):
        return self.__get_metadata_by_key_with_int_default(PreservedMetadataKeys.HEART_BEAT_INTERVAL,
                                                           Constants.DEFAULT_HEART_BEAT_INTERVAL)

    def get_instance_heart_beat_timeout(self):
        return self.__get_metadata_by_key_with_int_default(PreservedMetadataKeys.HEART_BEAT_INTERVAL,
                                                           Constants.DEFAULT_HEART_BEAT_TIMEOUT)

    def get_ip_delete_timeout(self):
        return self.__get_metadata_by_key_with_int_default(PreservedMetadataKeys.IP_DELETE_TIMEOUT,
                                                           Constants.DEFAULT_IP_DELETE_TIMEOUT)

    def get_instance_id_generator(self):
        return self.__get_metadata_by_key_with_str_default(PreservedMetadataKeys.INSTANCE_ID_GENERATOR,
                                                           Constants.DEFAULT_INSTANCE_ID_GENERATOR)

    def contains_metadata(self, key: str) -> bool:
        if not self.metadata:
            return False
        return key in self.metadata.keys()

    def __get_metadata_by_key_with_int_default(self, key: str, default_value: int) -> int:
        if not self.metadata:
            return default_value
        value = self.metadata[key]

        pattern = re.compile(Constants.NUMBER_PATTERN)

        if value.strip() and re.match(pattern, value):
            return int(value)

        return default_value

    def __get_metadata_by_key_with_str_default(self, key: str, default_value: str) -> str:
        if not self.metadata:
            return default_value
        return self.metadata[key]
