import errno
import json
import logging
import os

from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, INVALID_INTERFACE_ERROR
from v2.nacos.naming.model.service import Service
from v2.nacos.naming.util.naming_client_util import get_service_cache_key
from v2.nacos.utils import file

logger = logging.getLogger(__name__)


class ConfigCachedFileType:
    CONFIG_CONTENT = "Config Content"
    CONFIG_ENCRYPTED_DATA_KEY = "Config Encrypted Data Key"


ENCRYPTED_DATA_KEY_FILE_NAME = "encrypted-data-key"

FAILOVER_FILE_SUFFIX = "_failover"


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


def get_failover(key: str, dir: str):
    file_path = get_config_fail_over_content_file_name(key, dir)
    return get_fail_over_config(file_path, ConfigCachedFileType.CONFIG_CONTENT)


def get_config_fail_over_content_file_name(cache_key: str, cache_dir: str):
    return get_file_name(cache_key, cache_dir) + FAILOVER_FILE_SUFFIX


def get_file_name(cache_key: str, cache_dir: str):
    return os.path.join(cache_dir, cache_key)


def get_encrypted_data_key_dir(cache_dir: str):
    return os.path.join(cache_dir, ENCRYPTED_DATA_KEY_FILE_NAME)


def get_config_encrypted_data_key_file_name(cache_key: str, cache_dir: str):
    return os.path.join(get_encrypted_data_key_dir(cache_dir), cache_key)


def get_fail_over_config(file_path: str, file_type: str):
    if not file.is_file_exist(file_path):
        error_msg = f"read {file_type} failed. cause file doesn't exist, file path: {file_path}."
        logger.warning(error_msg)
        return ""

    logger.warning(f"reading failover {file_type} from path:{file_path}")
    try:
        file_content = file.read_file(file_path)
        return file_content
    except Exception as e:
        logger.error(f"fail to read failover {file_type} from {file_path}, error:{e}")
        return ""


def get_config_fail_over_encrypted_data_key_file_name(cache_key, cache_dir):
    encrypted_data_key_file_name = get_config_encrypted_data_key_file_name(cache_key, cache_dir)
    return encrypted_data_key_file_name + FAILOVER_FILE_SUFFIX


def get_failover_encrypted_data_key(key: str, dir: str):
    file_path = get_config_fail_over_encrypted_data_key_file_name(key, dir)
    return get_fail_over_config(file_path, ConfigCachedFileType.CONFIG_ENCRYPTED_DATA_KEY)


def _write_config_to_file(file_name: str, content: str, file_type: str):
    if content.strip() == "":
        try:
            os.remove(file_name)
        except OSError as e:
            if e.errno == errno.ENOENT:
                logger.warning(f"No need to delete {file_type} cache file, file path {file_name}, file doesn't exist.")
            else:
                error_msg = f"Failed to delete {file_type} cache file, file path {file_name}, err: {e}"
                logger.error(error_msg)
                raise OSError(error_msg)
    else:
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(content)
        except IOError as e:
            error_msg = f"Failed to write {file_type} cache file, file name: {file_name}, value: {content}, err: {e}"
            logger.error(error_msg)
            raise IOError(error_msg)


def write_config_to_file(cache_key: str, cache_dir: str, content: str):
    file.mkdir_if_necessary(cache_dir)

    _write_config_to_file(get_file_name(cache_key, cache_dir), content, ConfigCachedFileType.CONFIG_CONTENT)


def write_encrypted_data_key_to_file(cache_key: str, cache_dir: str, content: str):
    file.mkdir_if_necessary(get_encrypted_data_key_dir(cache_dir))

    _write_config_to_file(get_config_encrypted_data_key_file_name(cache_key, cache_dir), content,
                          ConfigCachedFileType.CONFIG_ENCRYPTED_DATA_KEY)


def _read_config_from_file(file_name: str, file_type: str):
    if not os.path.isfile(file_name):
        raise NacosException(INVALID_INTERFACE_ERROR,
                             f"read cache file {file_type} failed. cause file doesn't exist, file path: {file_name}.")
    try:
        with open(file_name, 'rb') as file:
            file_content = file.read()
        return file_content.decode('utf-8')
    except IOError as e:
        raise NacosException(INVALID_INTERFACE_ERROR,
                             f"get {file_type} from cache failed, filePath:{file_name}, error:{str(e)}")


def read_config_from_file(cache_key: str, cache_dir: str):
    file_name = get_file_name(cache_key, cache_dir)
    return _read_config_from_file(file_name, ConfigCachedFileType.CONFIG_CONTENT)


def read_encrypted_data_key_from_file(cache_key: str, cache_dir: str):
    file_name = get_file_name(cache_key, cache_dir)
    return _read_config_from_file(file_name, ConfigCachedFileType.CONFIG_ENCRYPTED_DATA_KEY)
