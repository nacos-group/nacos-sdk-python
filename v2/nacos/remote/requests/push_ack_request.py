from typing import Optional

from v2.nacos.remote.requests import request
from v2.nacos.remote.utils import remote_request_type


class PushAckRequest(request.Request):
    requestId: Optional[str]
    success: Optional[bool]
    exception: Optional[Exception]

    @staticmethod
    def build(request_id: str, success: bool):
        new_request = PushAckRequest(requestId=request_id, success=success)
        return new_request

    def get_request_id(self) -> str:
        return self.requestId

    def set_request_id(self, request_id: str) -> None:
        self.requestId = request_id

    def is_success(self) -> bool:
        return self.success

    def set_success(self, success: bool) -> None:
        self.success = success

    def get_exception(self) -> Exception:
        return self.exception

    def set_exception(self, exception: Exception) -> None:
        self.exception = exception

    def get_module(self):
        return "internal"

    def get_remote_type(self):
        return remote_request_type["PushAck"]
