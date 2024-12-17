from v2.nacos.common.constants import Constants


def get_group_name(service_name, group_name):
    return f"{group_name}{Constants.SERVICE_INFO_SPLITER}{service_name}"


def get_service_cache_key(service_name, clusters):
    if not clusters:
        return service_name
    return f"{service_name}{Constants.SERVICE_INFO_SPLITER}{clusters}"
