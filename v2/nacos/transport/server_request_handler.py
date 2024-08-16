import logging
from typing import Any
from abc import ABC, abstractmethod
from v2.nacos.transport.model.internal_request import ConnectResetRequest
from v2.nacos.transport.model.internal_response import ConnectResetResponse
from v2.nacos.transport.model.server_info import ServerInfo
from v2.nacos.common.constants import Constants

class IServerRequestHandler(ABC):
    
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def request_reply(self, request, rpc_client) -> Any:
        pass

class ConnectResetRequestHandler(IServerRequestHandler):
    def name(self) -> str:
        return "ConnectResetRequestHandler"

    def request_reply(self, request, rpc_client) -> Any:
        if isinstance(request, ConnectResetRequest) and rpc_client.is_running():
            server_ip = request.server_ip
            if server_ip != "":
                server_port = int(request.server_port)
                rpc_client._switch_server_async(server_info=ServerInfo(server_ip, server_port), on_request_fail = False)
            else:
                rpc_client._switch_server_async(server_info=ServerInfo("",0), on_request_fail = True)
                
            connect_reset_response = ConnectResetResponse()
            connect_reset_response.result_code = Constants.RESPONSE_CODE_SUCCESS
            return connect_reset_response
        return None