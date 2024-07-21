from .remote.rpc_request import IRequest


class MockConnection:

    def request(self, request: IRequest, timeout_millis: int,
                client: RpcClient) -> Any:
        return None, None

    def close(self) -> None:
        pass

    def get_connection_id(self) -> str:
        return ""

    def get_server_info(self) -> ServerInfo:
        return ServerInfo()

    def set_abandon(self, flag: bool) -> None:
        pass
