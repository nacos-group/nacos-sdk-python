from typing import Dict
from v2.nacos.common.model.response import Response


class ConnectResetResponse(Response):
    def __init__(self):
        super().__init__()

    def get_response_type(self) -> str:
        return "ConnectResetResponse"