from abc import ABC, abstractmethod
from v2.nacos.utils.common_util import to_json_string

class IResponse(ABC):
    @abstractmethod
    def get_response_type(self) -> str:
        pass

    @abstractmethod
    def set_request_id(self, request_id: str):
        pass

    @abstractmethod
    def get_body(self) -> str:
        pass

    @abstractmethod
    def get_error_code(self) -> int:
        pass

    @abstractmethod
    def is_success(self) -> bool:
        pass

    @abstractmethod
    def set_success(self, success: bool):
        pass

    @abstractmethod
    def get_result_code(self) -> int:
        pass

    @abstractmethod
    def get_message(self) -> str:
        pass

class Response(IResponse):
    def __init__(self):
        self.result_code = 0
        self.error_code = 0
        self.success = False
        self.message = ""
        self.request_id = ""

    def set_request_id(self, request_id: str):
        self.request_id = request_id

    def get_body(self) -> str:
        return to_json_string(self.__dict__)

    def is_success(self) -> bool:
        return self.success

    def set_success(self, success: bool):
        self.success = success

    def get_error_code(self) -> int:
        return self.error_code

    def get_result_code(self) -> int:
        return self.result_code

    def get_message(self) -> str:
        return self.message
    
    def get_response_type(self) -> str:
        pass