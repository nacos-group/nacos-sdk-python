from v2.nacos.common.constants import Constants
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.naming.dtos.instance import Instance


class NamingUtils:
    @staticmethod
    def get_grouped_name(service_name: str, group_name: str) -> str:
        pass

    @staticmethod
    def get_service_name(service_name_with_group: str) -> str:
        pass

    @staticmethod
    def get_group_name(service_name_with_group: str) -> str:
        pass

    @staticmethod
    def check_service_name_format(combine_service_name: str) -> None:
        pass

    @staticmethod
    def get_grouped_name_optional(service_name: str, group_name: str) -> str:
        return group_name + Constants.SERVICE_INFO_SPLITER + service_name

    @staticmethod
    def check_instance_is_legal(instance: Instance) -> None:
        if instance.get_instance_heart_beat_timeout() < instance.get_instance_heart_beat_interval() or \
                instance.get_ip_delete_timeout() < instance.get_instance_heart_beat_interval():
            raise NacosException(
                NacosException.INVALID_PARAM + \
                "Instance 'heart beat interval' must less than 'heart beat timeout' and 'ip delete timeout'."
            )
