from v2.nacos.utils.env_util import EnvUtil

system_properties = EnvUtil().get_system_properties()


class NetUtils:
    CLIENT_NAMING_LOCAL_IP_PROPERTY = "com.alibaba.nacos.client.naming.local.ip"

    @staticmethod
    def get_local_ip():
        return system_properties.get(NetUtils.CLIENT_NAMING_LOCAL_IP_PROPERTY)
