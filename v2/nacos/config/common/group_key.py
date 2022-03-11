from v2.nacos.exception.nacos_exception import NacosException


class GroupKey:
    PLUS = '+'

    PERCENT = '%'

    TWO = '2'

    B = 'B'

    FIVE = '5'

    @staticmethod
    def get_key(data_id: str, group: str, datum_str: str) -> str:
        return GroupKey.__do_get_key(data_id, group, datum_str)

    @staticmethod
    def get_key_tenant(data_id: str, group: str, tenant: str) -> str:
        return GroupKey.__do_get_key(data_id, group, tenant)

    @staticmethod
    def parse_key(group_key: str) -> list:
        sb = ""
        data_id = None
        group = None
        tenant = None

        i = 0
        while i < len(group_key):
            c = group_key[i]
            if GroupKey.PLUS == c:
                if not data_id:
                    data_id = sb
                    sb = ""
                elif not group:
                    group = sb
                    sb = ""
                else:
                    raise NacosException("invalid group_key:"+group_key)
            elif GroupKey.PERCENT == c:
                i += 1
                next_c = group_key[i]
                i += 1
                next_next_c = group_key[i]
                if GroupKey.TWO == next_c and GroupKey.B == next_next_c:
                    sb += GroupKey.PLUS
                elif GroupKey.TWO == next_c and GroupKey.FIVE == next_next_c:
                    sb += GroupKey.PERCENT
                else:
                    raise NacosException("invalid group_key:"+group_key)
            else:
                sb += c

        if not group:
            group = sb
        else:
            tenant = sb

        if not data_id:
            raise NacosException("invalid data_id")
        if not group:
            raise NacosException("invalid group")
        return [data_id, group, tenant]

    @staticmethod
    def url_encode(string: str) -> str:
        sb = ""
        for c in string:
            if GroupKey.PLUS == c:
                sb += "%2B"
            elif GroupKey.PERCENT == c:
                sb += "%25"
            else:
                sb += c
        return sb

    @staticmethod
    def __do_get_key(data_id: str, group: str, datum_str: str) -> str:
        if not data_id or not data_id.strip():
            raise NacosException("invalid dataId")
        if not group or not group.strip():
            raise NacosException("invalid group")

        sb = ""
        sb += GroupKey.url_encode(data_id)
        sb += GroupKey.PLUS
        sb += GroupKey.url_encode(group)
        if datum_str:
            sb += GroupKey.PLUS
            sb += GroupKey.url_encode(datum_str)
        return sb
