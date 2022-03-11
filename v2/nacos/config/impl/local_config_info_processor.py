import os

from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.utils.arg_util import arg_parser

system_args_parser = arg_parser.parse_args()


class LocalConfigInfoProcessor:
    SUFFIX = "_nacos"

    ENV_CHILD = "snapshot"

    FAILOVER_FILE_CHILD_1 = "data"

    FAILOVER_FILE_CHILD_2 = "config-data"

    FAILOVER_FILE_CHILD_3 = "config-data-tenant"

    SNAPSHOT_FILE_CHILD_1 = "snapshot"

    SNAPSHOT_FILE_CHILD_2 = "snapshot-tenant"

    USER_HOME = system_args_parser.user_home

    LOCAL_FILEROOT_PATH = os.path.join(USER_HOME, "nacos", "config")

    LOCAL_SNAPSHOT_PATH = os.path.join(USER_HOME, "nacos", "config")

    def __init__(self, logger):
        self.logger = logger

    def get_failover(self, server_name, data_id, group, tenant):
        local_path = self.get_failover_file(server_name, data_id, group, tenant)
        if not os.path.exists(local_path) or not os.path.isfile(local_path):
            return

        try:
            return self.read_file(local_path)
        except NacosException as e:
            self.logger.error("[" + server_name + "] get failover error, " + local_path + str(e))
            return

    def get_snapshot(self, name, data_id, group, tenant):
        file_path = self.get_snapshot_file(name, data_id, group, tenant)
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return

        try:
            return self.read_file(file_path)
        except NacosException as e:
            self.logger.error("[" + name + "] get snapshot error" + file_path + str(e))
            return

    def save_snapshot(self, env_name, data_id, group, tenant, config):
        file_path = self.get_snapshot_file(env_name, data_id, group, tenant)

        if not config:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except NacosException as e:
                    self.logger.error("[" + env_name + "] delete snapshot error" + str(e))
        else:
            try:
                if not file_path or not os.path.exists(file_path):
                    parent_path, file_name = os.path.split(file_path)
                    if not os.path.exists(parent_path):
                        os.makedirs(parent_path)
                    with open(file_path, "w", encoding='utf=8') as f:
                        f.write(config)
            except NacosException as e:
                self.logger.error("[" + env_name + "] save snapshot error" + file_path + str(e))

    def clean_all_snapshot(self) -> None:
        try:
            files = os.listdir(LocalConfigInfoProcessor.LOCAL_SNAPSHOT_PATH)
            if not files or len(files) == 0:
                return

            for file in files:
                if file.endswith(LocalConfigInfoProcessor.SUFFIX):
                    os.remove(file)
        except NacosException as e:
            self.logger.error("clean all snapshot error, " + str(e))

    @staticmethod
    def get_failover_file(server_name, data_id, group, tenant):
        tmp = os.path.join(LocalConfigInfoProcessor.LOCAL_SNAPSHOT_PATH, server_name + LocalConfigInfoProcessor.SUFFIX)
        if not tenant:
            tmp = os.path.join(tmp, LocalConfigInfoProcessor.SNAPSHOT_FILE_CHILD_1)
        else:
            tmp = os.path.join(tmp, LocalConfigInfoProcessor.SNAPSHOT_FILE_CHILD_2, tenant)
        return os.path.join(tmp, group, data_id)

    @staticmethod
    def get_snapshot_file(env_name, data_id, group, tenant):
        tmp = os.path.join(LocalConfigInfoProcessor.LOCAL_SNAPSHOT_PATH, env_name+LocalConfigInfoProcessor.SUFFIX)
        if not tenant:
            tmp = os.path.join(tmp, LocalConfigInfoProcessor.SNAPSHOT_FILE_CHILD_1)
        else:
            tmp = os.path.join(tmp, LocalConfigInfoProcessor.SNAPSHOT_FILE_CHILD_2, tenant)
        return os.path.join(tmp, group, data_id)

    @staticmethod
    def read_file(file_path):
        with open(file_path, "r", encoding='utf-8') as f:
            file_content = f.read()
            return str(file_content)

