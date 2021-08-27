class GroupKey:
    PLUS = '+'

    PERCENT = '%'

    TWO = '2'

    B = 'B'

    FIVE = '5'

    @staticmethod
    def get_key(data_id: str, group: str, datum_str: str) -> str:
        pass

    @staticmethod
    def get_key_tenant(data_id: str, group: str, tenant: str) -> str:
        pass

    @staticmethod
    def parse_key(group_key: str) -> list:
        pass

    @staticmethod
    def url_encode(string: str) -> str:
        pass

    @staticmethod
    def __do_get_key(self, data_id: str, group: str, datum_str: str) -> str:
        pass
