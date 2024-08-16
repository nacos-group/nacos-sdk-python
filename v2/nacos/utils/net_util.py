import socket
import os
import logging
from functools import lru_cache

class NetUtils:

    localIP = ""
    
    @staticmethod
    @lru_cache(maxsize=1)
    def get_local_ip():
        global localIP
        if localIP:  # 如果已经获取过本地IP，则直接返回
            return localIP

        try:
            # 获取所有网络接口
            net_interfaces = socket.getaddrinfo(socket.gethostname(), None)
        except socket.gaierror as err:
            logging.error(f"get Interfaces failed, err: {err}")
            return ""

        for fam, type_, proto, canonname, sockaddr in net_interfaces:
            # 检查网络接口是否启用且不是回环接口
            if type_ == socket.SOCK_STREAM and not sockaddr[0].startswith("127."):
                try:
                    # 获取网络接口的地址列表
                    addrs = socket.getaddrinfo(sockaddr[0], None)
                except socket.gaierror as err:
                    logging.error(f"get InterfaceAddress failed, err: {err}")
                    continue

                for addr in addrs:
                    ip = addr[4][0]
                    if ip != '127.0.0.1':  # 排除回环地址
                        localIP = ip
                        logging.info(f"Local IP: {localIP}")
                        break

        # 如果没有找到合适的IP，返回空字符串
        return localIP if localIP else ""