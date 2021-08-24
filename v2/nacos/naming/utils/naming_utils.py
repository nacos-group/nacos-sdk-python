from v2.nacos.common.constants import Constants
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.naming.dtos.instance import Instance


class NamingUtils:
    @staticmethod
    def get_grouped_name(service_name: str, group_name: str) -> str:
        if not group_name.strip():
            raise NacosException("Param 'service_name' is illegal, service_name is blank")
        if not service_name.strip():
            raise NacosException("Param 'group_name' is illegal, group_name is blank")

        result_grouped_name = group_name.strip() + Constants.SERVICE_INFO_SPLITER + service_name.strip()
        return result_grouped_name

    @staticmethod
    def get_service_name(service_name_with_group: str) -> str:
        if not service_name_with_group or not service_name_with_group.strip():
            return ""
        if Constants.SERVICE_INFO_SPLITER not in service_name_with_group:
            return service_name_with_group
        return service_name_with_group.split(Constants.SERVICE_INFO_SPLITER)[1]

    @staticmethod
    def get_group_name(service_name_with_group: str) -> str:
        if not service_name_with_group or not service_name_with_group.strip():
            return ""

        if Constants.SERVICE_INFO_SPLITER not in service_name_with_group:
            return Constants.DEFAULT_GROUP

        return service_name_with_group.split(Constants.SERVICE_INFO_SPLITER)[0]

    @staticmethod
    def check_service_name_format(combine_service_name: str) -> None:
        split = combine_service_name.split(Constants.SERVICE_INFO_SPLITER)
        if len(split) <= 1:
            raise NacosException("Param 'service_name' is illegal, it should be format as 'group_name@@service_name'")
        if not split[0].strip():
            raise NacosException("Param 'service_name' is illegal, group_name can't be empty")
        if not split[1].split():
            raise NacosException("Param 'service_name' is illegal, service_name can't be empty")

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
