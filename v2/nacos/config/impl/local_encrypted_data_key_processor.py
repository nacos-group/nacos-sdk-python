import os

from v2.nacos.config.impl.local_config_info_processor import LocalConfigInfoProcessor
from v2.nacos.exception.nacos_exception import NacosException


class LocalEncryptedDataKeyProcessor(LocalConfigInfoProcessor):
    FAILOVER_CHILD_1 = "encrypted-data-key"

    FAILOVER_CHILD_2 = "failover"

    FAILOVER_CHILD_3 = "failover-tenant"

    SNAPSHOT_CHILD_1 = "encrypted-data-key"

    SNAPSHOT_CHILD_2 = "snapshot"

    SNAPSHOT_CHILD_3 = "snapshot-tenant"

    SUFFIX = "_nacos"

    def get_encrypt_data_key_failover(self, env_name: str, data_id: str, group: str, tenant: str):
        file_path = self.__get_encrypt_data_key_failover_file(env_name, data_id, group, tenant)
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return

        try:
            return self.read_file(file_path)
        except NacosException as e:
            self.logger.error("[" + env_name + "] get encrypt data key failover error, " + str(e))
            return

    def get_encrypt_data_key_snapshot(self, env_name: str, data_id: str, group: str, tenant: str):
        file_path = self.__get_encrypt_data_key_snapshot_file(env_name, data_id, group, tenant)
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return

        try:
            return self.read_file(file_path)
        except NacosException as e:
            self.logger.error("[" + env_name + "] get encrypt data key snapshot error, " + str(e))
            return

    def save_encrypt_data_key_snapshot(
            self, env_name: str, data_id: str, group: str, tenant: str, encrypt_data_key: str
    ) -> None:
        file_path = self.__get_encrypt_data_key_snapshot_file(env_name, data_id, group, tenant)
        try:
            if not encrypt_data_key:
                try:
                    os.remove(file_path)
                except NacosException as e:
                    self.logger.error("[" + env_name + "] delete encrypt data key snapshot error" + str(e))
            else:
                if not file_path or not os.path.exists(file_path):
                    parent_path, file_name = os.path.split(file_path)
                    if not os.path.exists(parent_path):
                        os.makedirs(parent_path)
                    os.mknod(file_name)
                    with open(file_path, "w", encoding='utf=8') as f:
                        f.write(encrypt_data_key)
        except NacosException as e:
            self.logger.error("[" + env_name + "] save encrypt data key snapshot error" + file_path + str(e))

    @staticmethod
    def __get_encrypt_data_key_failover_file(env_name: str, data_id: str, group: str, tenant: str) -> str:
        tmp = os.path.join(
            LocalEncryptedDataKeyProcessor.LOCAL_SNAPSHOT_PATH, env_name+LocalEncryptedDataKeyProcessor.SUFFIX
        )

        if not tenant:
            tmp = os.path.join(tmp, LocalEncryptedDataKeyProcessor.FAILOVER_CHILD_2)
        else:
            tmp = os.path.join(tmp, LocalEncryptedDataKeyProcessor.FAILOVER_CHILD_3, tenant)

        return os.path.join(tmp, group, data_id)

    @staticmethod
    def __get_encrypt_data_key_snapshot_file(env_name: str, data_id: str, group: str, tenant: str) -> str:
        tmp = os.path.join(
            LocalEncryptedDataKeyProcessor.LOCAL_SNAPSHOT_PATH, env_name+LocalEncryptedDataKeyProcessor.SUFFIX
        )

        if not tenant:
            tmp = os.path.join(tmp, LocalEncryptedDataKeyProcessor.SNAPSHOT_CHILD_2)
        else:
            tmp = os.path.join(tmp, LocalEncryptedDataKeyProcessor.SNAPSHOT_CHILD_3, tenant)

        return os.path.join(tmp, group, data_id)
