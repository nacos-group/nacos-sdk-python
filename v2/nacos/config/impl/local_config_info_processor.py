class LocalConfigInfoProcessor:
    SUFFIX = "_nacos"

    ENV_CHILD = "snapshot"

    FAILOVER_FILE_CHILD_1 = "data"

    FAILOVER_FILE_CHILD_2 = "config-data"

    FAILOVER_FILE_CHILD_3 = "config-data-tenant"

    SNAPSHOT_FILE_CHILD_1 = "snapshot"

    SNAPSHOT_FILE_CHILD_2 = "snapshot-tenant"

    @staticmethod
    def get_failover(server_name: str, data_id: str, group: str, tenant: str) -> str:
        pass

    @staticmethod
    def get_snapshot(name: str, data_id: str, group: str, tenant: str) -> str:
        pass

    @staticmethod
    def save_snapshot(env_name: str, data_id: str, group: str, tenant: str, config: str) -> None:
        pass

    @staticmethod
    def clean_all_snapshot() -> None:
        pass

    @staticmethod
    def get_failover_file(server_name: str, data_id: str, group: str, tenant: str):
        pass

    @staticmethod
    def get_snapshot_file(env_name: str, data_id: str, group: str, tenant: str):
        pass
