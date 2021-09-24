import re
from typing import Optional

from pydantic import BaseModel

from v2.nacos.common.constants import Constants
from v2.nacos.common.preserved_metadata_keys import PreservedMetadataKeys


class Instance(BaseModel):
    instanceId: Optional[str]
    ip: Optional[str]
    port: Optional[int]
    weight: float = 1.0
    healthy: bool = True
    enabled: bool = True
    ephemeral: bool = True
    clusterName: Optional[str]
    serviceName: Optional[str]
    metadata: dict = {}

    def __str__(self):
        return \
            "Instance{instanceId='" + str(self.instanceId) + "', ip='" + str(self.ip) + "', port=" + str(self.port) + \
            ", weight=" + str(self.weight) + ", healthy=" + str(self.healthy) + ", enabled=" + str(self.enabled) + \
            ", ephemeral=" + str(self.ephemeral) + ", clusterName='" + str(self.clusterName) + "', serviceName='" + \
            str(self.serviceName) + "', metadata=" + str(self.metadata) + "}"

    def to_inet_addr(self) -> str:
        return self.ip + ":" + str(self.port)

    def is_ephemeral(self) -> bool:
        return self.ephemeral

    def get_weight(self) -> float:
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

    def is_healthy(self) -> bool:
        return self.healthy

    def is_enabled(self) -> bool:
        return self.enabled

    def __get_metadata_by_key_with_int_default(self, key: str, default_value: int) -> int:
        if not self.metadata:
            return default_value
        value = self.metadata.get(key)

        pattern = re.compile(Constants.NUMBER_PATTERN)

        if value and value.strip() and re.match(pattern, value):
            return int(value)

        return default_value

    def __get_metadata_by_key_with_str_default(self, key: str, default_value: str) -> str:
        if not self.metadata:
            return default_value
        return self.metadata[key]
