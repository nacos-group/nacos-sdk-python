from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.constants import Constants

from v2.nacos.config.encryption.kms_handler import KMSHandler
from v2.nacos.config.filter.config_filter import IConfigFilter
from v2.nacos.config.model.config_param import ConfigParam, HandlerParam, UsageType


def _param_check(param: ConfigParam):
    if param.data_id.startswith(Constants.CIPHER_PRE_FIX) and len(param.content.strip()) != 0:
        return False
    return True


class ConfigEncryptionFilter(IConfigFilter):

    def __init__(self, client_config: ClientConfig):
        self.kms_handler = KMSHandler(client_config.kms_config)

    def do_filter(self, param: ConfigParam) -> None:
        if param.usage_type == UsageType.request_type.value:
            encryption_param = HandlerParam(data_id=param.data_id, content=param.content, key_id=param.kms_key_id)
            self.kms_handler.encrypt_handler(encryption_param)
            param.content = encryption_param.content
            param.encrypted_data_key = encryption_param.encrypted_data_key

        elif param.usage_type == UsageType.response_type.value:
            decryption_param = HandlerParam(data_id=param.data_id, content=param.content,
                                            encrypted_data_key=param.encrypted_data_key)
            self.kms_handler.decrypt_handler(decryption_param)
            param.content = decryption_param.content

    def get_order(self) -> int:
        return 0

    def get_filter_name(self) -> str:
        return "defaultConfigEncryptionFilter"
