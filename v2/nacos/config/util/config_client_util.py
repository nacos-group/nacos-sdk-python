from v2.nacos.common.constants import Constants


def get_config_cache_key(data_id: str, group: str, tenant: str):
    return f"{data_id}{Constants.CONFIG_INFO_SPLITER}{group}{Constants.CONFIG_INFO_SPLITER}{tenant}"
