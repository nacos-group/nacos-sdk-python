import re

from pydantic import BaseModel

from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.common.preserved_metadata_key import PreservedMetadataKeys


class Instance(BaseModel):
    instanceId: str = ''
    ip: str
    port: int
    weight: float = 1.0
    healthy: bool = True
    enabled: bool = True
    ephemeral: bool = True
    clusterName: str = ''
    serviceName: str = ''
    metadata: dict = {}

    def __str__(self):
        return f"Instance({', '.join(f'{key}={value!r}' for key, value in self.__dict__.items())})"

    def to_inet_addr(self):
        return self.ip + ":" + str(self.port)

    def is_ephemeral(self) -> bool:
        return self.ephemeral

    def get_weight(self):
        return self.weight

    def add_metadata(self, key: str, value: str) -> None:
        if self.metadata is None:
            self.metadata = {}
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

    def check_instance_is_legal(self):
        if self.get_instance_heart_beat_timeout() < self.get_instance_heart_beat_interval() or \
                self.get_ip_delete_timeout() < self.get_instance_heart_beat_interval():
            raise NacosException(
                INVALID_PARAM,
                "Instance 'heart beat interval' must less than 'heart beat timeout' and 'ip delete timeout'."
            )
        self.fill_default_value()

        if not self.ip or len(self.ip) == 0:
            raise NacosException(INVALID_PARAM, "Instance 'ip' can not be empty.")

        if self.port < 0 or self.port > 65535:
            raise NacosException(INVALID_PARAM, "Instance 'port' must be between 0 and 65535.")

    def fill_default_value(self):
        if self.clusterName is None or len(self.clusterName) == 0:
            self.clusterName = Constants.DEFAULT_CLUSTER_NAME

    def contains_metadata(self, key: str) -> bool:
        if not self.metadata:
            return False
        return key in self.metadata.keys()

    def __get_metadata_by_key_with_int_default(self, key: str, default_value: int) -> int:
        if not self.metadata or key not in self.metadata:
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
