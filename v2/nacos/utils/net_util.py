import socket
from functools import lru_cache

import psutil

from v2.nacos.common.nacos_exception import NacosException, INVALID_INTERFACE_ERROR


class NetUtils:
    @staticmethod
    @lru_cache(maxsize=1)
    def get_local_ip():
        try:
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                        return addr.address
            raise NacosException(INVALID_INTERFACE_ERROR, "no valid non-loopback IPv4 interface found")
        except socket.gaierror as err:
            raise NacosException(INVALID_INTERFACE_ERROR, f"failed to query local IP address, error: {str(err)}")
