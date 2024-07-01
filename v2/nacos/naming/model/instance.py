import re

from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_PARAM
from v2.nacos.common.preserved_metadata_key import PreservedMetadataKeys


class Instance:
    def __init__(self, service_name=None, ip=None, port=None, cluster_name=None, weight=1.0, healthy=True, enable=True,
                 ephemeral=True, metadata=None):
        if metadata is None:
            metadata = {}
        self.ip = ip
        self.port = port
        self.weight = weight
        self.healthy = healthy
        self.enable = enable
        self.ephemeral = ephemeral
        self.cluster_name = cluster_name
        self.service_name = service_name
        self.metadata = metadata

    def __str__(self):
        return f"Instance({', '.join(f'{key}={value!r}' for key, value in self.__dict__.items())})"

    def to_inet_addr(self):
        return self.ip + ":" + self.port

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
