from v2.nacos.utils.arg_util import arg_parser

system_args_parser = arg_parser.parse_args()


class NetUtils:
    CLIENT_NAMING_LOCAL_IP_PROPERTY = "com.alibaba.nacos.client.naming.local.ip"

    @staticmethod
    def get_local_ip():
        return system_args_parser.com_alibaba_nacos_client_naming_local_ip
