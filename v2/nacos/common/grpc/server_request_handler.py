import re
import json
import logging
from typing import Any


class IServerRequestHandler:
    def name(self) -> str:
        pass

    def request_reply(self, request: Any, rpc_client: Any) -> Any:
        pass

class ConnectResetRequestHandler(IServerRequestHandler):
    def name(self) -> str:
        return "ConnectResetRequestHandler"

    def request_reply(self, request: Any, rpc_client: Any) -> Any:
        # 检查request是否是ConnectResetRequest的实例
        if isinstance(request, dict) and "ServerIp" in request and "ServerPort" in request:
            server_ip = request["ServerIp"]
            server_port = int(request["ServerPort"])
            rpc_client.mux.Lock()
            try:
                if rpc_client.is_running():
                    rpc_client.switch_server_async(server_info=ServerInfo(server_ip, server_port), force=False)
            finally:
                rpc_client.mux.Unlock()
            return {"ResultCode": constant.RESPONSE_CODE_SUCCESS}
        return None

class ClientDetectionRequestHandler(IServerRequestHandler):
    def name(self) -> str:
        return "ClientDetectionRequestHandler"

    def request_reply(self, request: Any, _:Any) -> Any:
        if isinstance(request, dict) and "ClientDetectionRequest" in request:
            return {"ResultCode": constant.RESPONSE_CODE_SUCCESS}
        return None

class NamingPushRequestHandler(IServerRequestHandler):
    def __init__(self, service_info_holder: Any):
        self.service_info_holder = service_info_holder

    def name(self) -> str:
        return "NamingPushRequestHandler"

    def request_reply(self, request: Any, client: Any) -> Any:
        if isinstance(request, dict) and "ServiceInfo" in request:
            self.service_info_holder.process_service(request["ServiceInfo"])
            logging.debug(f"naming push response success ackId->{request['GetRequestId']()}")
            return {"ResultCode": constant.RESPONSE_CODE_SUCCESS, "Success": True}
        return None

class ServerInfo:
    def __init__(self, server_ip: str, server_port: int):
        self.server_ip = server_ip
        self.server_port = server_port

class constant:
    RESPONSE_CODE_SUCCESS = 200