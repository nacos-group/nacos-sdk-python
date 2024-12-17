from v2.nacos.common.constants import Constants


class ServerInfo:
    def __init__(self, server_ip: str, server_port: int):
        self.server_ip = server_ip
        self.server_port = server_port

    def get_address(self):
        return self.server_ip + Constants.COLON + str(self.server_port)

    def get_server_ip(self):
        return self.server_ip

    def set_server_ip(self, server_ip):
        self.server_ip = server_ip

    def get_server_port(self):
        return self.server_port

    def set_server_port(self, server_port):
        self.server_port = server_port

    def __str__(self):
        return "{serverIp='" + str(self.server_ip) + "', server main port=" + str(self.server_port) + "}"
