import json
import logging
import os

from v2.nacos.common.constants import Constants
from v2.nacos.naming.model.service import Service

logger = logging.getLogger(__name__)


def read_services_from_file(cache_dir):
    try:
        files = os.listdir(cache_dir)
    except OSError as e:
        logger.error(f"failed to list naming cacheDir:{cache_dir}, err:{e}")
        return None

    service_map = {}
    for file_name in files:
        full_file_name = os.path.join(cache_dir, file_name)
        try:
            with open(full_file_name, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError as e:
            logger.error(f"failed to read name cache file:{file_name}, err:{e}")
            continue

        service = json_to_service(content)
        if service is None:
            continue

        cache_key = get_service_cache_key(service)
        service_map[cache_key] = service

    logger.info(f"finish loading name cache, total file size: {len(files)}")
    return service_map


def json_to_service(json_str):
    try:
        service_data = json.loads(json_str)
        service = Service(**service_data)
    except json.JSONDecodeError as e:
        logger.error(f"failed to parse json:{json_str}, err:{e}")
        return None

    if len(service.hosts) == 0:
        logger.warning(f"instance list is empty, json string:{json_str}")

    return service


def get_service_cache_key(service: Service):
    if service.clusters is None:
        return service.group_name + Constants.SERVICE_INFO_SPLITER + service.service_name
    else:
        return service.group_name + Constants.SERVICE_INFO_SPLITER + service.service_name + Constants.SERVICE_INFO_SPLITER + service.clusters
