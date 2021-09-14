import re

from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.property_key_constants import PropertyKeyConstants


class ValidatorUtils:
    CONTEXT_PATH_MATCH = "(\\/)\\1+"

    @staticmethod
    def check_init_param(properties: dict):
        ValidatorUtils.check_context_path(properties.get(PropertyKeyConstants.CONTEXT_PATH))

    @staticmethod
    def check_context_path(context_path):
        if not context_path:
            return

        if re.search(ValidatorUtils.CONTEXT_PATH_MATCH, context_path):
            raise NacosException("Illegal url path expression")
