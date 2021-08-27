class NetUtils:
    CLIENT_NAMING_LOCAL_IP_PROPERTY = "com.alibaba.nacos.client.naming.local.ip"
    LEGAL_LOCAL_IP_PROPERTY = "java.net.preferIPv6Addresses"
    DEFAULT_SOLVE_FAILED_RETURN = "resolve_failed"

    def get_local_ip(self):
        # todo
        return "192.168.220.22"

    def find_first_non_loop_back_address(self):
        pass
