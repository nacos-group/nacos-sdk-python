class ServerInfo: 
    def __init__(self, server_ip: str, server_port: int,
                 server_grpc_port: int):
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_grpc_port = server_grpc_port