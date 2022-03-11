from v2.nacos.exception.nacos_exception import NacosException


class ParamUtils:
    VALID_CHARS = ['_', '-', '.', ':']

    CONTENT_INVALID_MSG = "content invalid"

    DATAID_INVALID_MSG = "dataId invalid"

    TENANT_INVALID_MSG = "tenant invalid"

    BETAIPS_INVALID_MSG = "betaIps invalid"

    GROUP_INVALID_MSG = "group invalid"

    DATUMID_INVALID_MSG = "datumId invalid"

    @staticmethod
    def is_valid(param: str) -> bool:
        if not param:
            return False
        for ch in param:
            if not ch.isdigit() and not ch.isalpha() and not ParamUtils.__is_valid_chars(ch):
                return False
        return True

    @staticmethod
    def __is_valid_chars(ch: str) -> bool:
        return True if ch in ParamUtils.VALID_CHARS else False

    @staticmethod
    def check_tdg(tenant: str, data_id: str, group: str) -> None:
        ParamUtils.check_tenant(tenant)
        if ParamUtils.is_blank(data_id) or not ParamUtils.is_valid(data_id):
            raise NacosException(str(NacosException.CLIENT_INVALID_PARAM) + " " + ParamUtils.DATAID_INVALID_MSG)
        if ParamUtils.is_blank(group) or not ParamUtils.is_valid(group):
            raise NacosException(str(NacosException.CLIENT_INVALID_PARAM) + " " + ParamUtils.GROUP_INVALID_MSG)

    @staticmethod
    def check_key_param(data_id: str, group: str) -> None:
        if ParamUtils.is_blank(data_id) or not ParamUtils.is_valid(data_id):
            raise NacosException(str(NacosException.CLIENT_INVALID_PARAM) + " " + ParamUtils.DATAID_INVALID_MSG)
        if ParamUtils.is_blank(group) or not ParamUtils.is_valid(group):
            raise NacosException(str(NacosException.CLIENT_INVALID_PARAM) + " " + ParamUtils.GROUP_INVALID_MSG)

    @staticmethod
    def check_key_param_with_datum_id(data_id: str, group: str, datum_id: str) -> None:
        if ParamUtils.is_blank(data_id) or not ParamUtils.is_valid(data_id):
            raise NacosException(str(NacosException.CLIENT_INVALID_PARAM) + " " + ParamUtils.DATAID_INVALID_MSG)
        if ParamUtils.is_blank(group) or not ParamUtils.is_valid(group):
            raise NacosException(str(NacosException.CLIENT_INVALID_PARAM) + " " + ParamUtils.GROUP_INVALID_MSG)
        if ParamUtils.is_blank(datum_id) or not ParamUtils.is_valid(datum_id):
            raise NacosException(str(NacosException.CLIENT_INVALID_PARAM) + " " + ParamUtils.DATUMID_INVALID_MSG)

    @staticmethod
    def check_key_params(data_ids: list, group: str) -> None:
        if not data_ids or len(data_ids) == 0:
            raise NacosException(str(NacosException.CLIENT_INVALID_PARAM) + " dataIds invalid")
        for data_id in data_ids:
            if ParamUtils.is_blank(data_id) or not ParamUtils.is_valid(data_id):
                raise NacosException(str(NacosException.CLIENT_INVALID_PARAM) + " " + ParamUtils.DATAID_INVALID_MSG)
        if ParamUtils.is_blank(group) or not ParamUtils.is_valid(group):
            raise NacosException(str(NacosException.CLIENT_INVALID_PARAM) + " " + ParamUtils.GROUP_INVALID_MSG)

    @staticmethod
    def check_param(data_id: str, group: str, content: str) -> None:
        ParamUtils.check_key_param(data_id, group)
        if ParamUtils.is_blank(content):
            raise NacosException(str(NacosException.CLIENT_INVALID_PARAM) + " " + ParamUtils.CONTENT_INVALID_MSG)

    @staticmethod
    def check_param_with_datum_id(data_id: str, group: str, datum_id: str, content: str) -> None:
        ParamUtils.check_key_param_with_datum_id(data_id, group, datum_id)
        if ParamUtils.is_blank(content):
            raise NacosException(str(NacosException.CLIENT_INVALID_PARAM) + " " + ParamUtils.CONTENT_INVALID_MSG)

    @staticmethod
    def check_tenant(tenant: str) -> None:
        if ParamUtils.is_blank(tenant) or not ParamUtils.is_valid(tenant):
            raise NacosException(str(NacosException.CLIENT_INVALID_PARAM) + " " + ParamUtils.TENANT_INVALID_MSG)

    @staticmethod
    def check_beta_ips(beta_ips: str) -> None:
        # todo
        pass

    @staticmethod
    def check_content(content: str) -> None:
        if ParamUtils.is_blank(content):
            raise NacosException(str(NacosException.CLIENT_INVALID_PARAM) + " " + ParamUtils.CONTENT_INVALID_MSG)

    @staticmethod
    def is_blank(param: str) -> bool:
        return False if param and param.strip() else True
