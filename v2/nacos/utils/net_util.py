import socket
from functools import lru_cache

from v2.nacos.common.nacos_exception import NacosException, INVALID_INTERFACE_ERROR


class NetUtils:
    @staticmethod
    @lru_cache(maxsize=1)
    def get_local_ip():
        try:
            # 获取所有网络接口
            net_interfaces = socket.getaddrinfo(socket.gethostname(), None)

            for fam, type_, proto, canonname, sockaddr in net_interfaces:
                # 检查网络接口是否启用且不是回环接口
                if fam == socket.AF_INET and type_ == socket.SOCK_STREAM and not sockaddr[0].startswith("127."):
                    return sockaddr[0]  # 直接返回找到的第一个合适IP
            raise NacosException(INVALID_INTERFACE_ERROR, "no valid non-loopback IPv4 interface found")
        except socket.gaierror as err:
            raise NacosException(INVALID_INTERFACE_ERROR, f"failed to query local IP address, error: {err}")
