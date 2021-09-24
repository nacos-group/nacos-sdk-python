import json
import os

from v2.nacos.common.constants import Constants
from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.naming.dtos.instance import Instance
from v2.nacos.naming.dtos.service_info import ServiceInfo
# from v2.nacos.utils.arg_util import ArgUtil
#
# system_properties = ArgUtil().get_system_properties()

from v2.nacos.utils.arg_util import arg_parser

system_args_parser = arg_parser.parse_args()


class DiskCache:
    LINE_SEPARATOR = "line.separator"

    def __init__(self, logger):
        self.logger = logger

    def write(self, dom: ServiceInfo, cache_dir: str):
        try:
            DiskCache.__make_sure_cache_dir_exists(cache_dir)
            file_path = os.path.join(cache_dir, dom.get_key_encoded())
            with open(file_path, "a", encoding="utf-8") as f:
                json_str = dom.get_json_from_server()
                if not json_str:
                    json_str = json.dumps(dom)
                f.write(json_str)
        except NacosException as e:
            self.logger.error("[NA] failed to write cache for dom: " + dom.get_name() + str(e))

    @staticmethod
    def get_line_separator():
        # return system_properties.get(DiskCache.LINE_SEPARATOR)
        return system_args_parser.line_separator

    def read(self, cache_dir: str):
        dom_map = {}
        try:
            files_dir = DiskCache.__make_sure_cache_dir_exists(cache_dir)
            files_list = os.listdir(files_dir)
            if not files_list:
                return dom_map

            for file in files_list:
                if not os.path.isfile(file):
                    continue

                if not (file.endswith(Constants.SERVICE_INFO_SPLITER + "meta") or
                        file.endswith(Constants.SERVICE_INFO_SPLITER + "special-url")):
                    dom = ServiceInfo()
                    dom.init_from_key(file)
                    ips = []
                    dom.set_hosts(ips)

                    new_format = None

                    try:
                        file_path = os.path.join(files_dir, file)
                        with open(file_path, "r", encoding="utf-8") as f:
                            json_strs = f.readlines()
                        for json_str in json_strs:
                            json_dict = json.loads(json_str)

                            new_format = ServiceInfo.build(json_dict)

                            new_instance = Instance(**json_dict)
                            ips.append(new_instance)
                    except NacosException as e:
                        self.logger.error("[NA] failed to read cache file from dom: " + file + str(e))

                    if new_format and new_format.get_name() and new_format.get_hosts():
                        dom_map[dom.get_key_default()] = new_format
                    elif dom.get_hosts():
                        dom_map[dom.get_key_default()] = dom
        except NacosException as e:
            self.logger.error("[NA] failed to read cache file" + str(e))

        return dom_map

    @staticmethod
    def __make_sure_cache_dir_exists(cache_dir: str):
        if not os.path.exists(cache_dir):
            try:
                os.makedirs(cache_dir)
            except OSError:
                raise EOFError("Failed to create cache dir: " + cache_dir)
        return cache_dir
