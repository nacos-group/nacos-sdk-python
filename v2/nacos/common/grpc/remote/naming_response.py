import json
from .rpc_response import Response
from ..model.service import Service

class ConnectResetResponse(Response):
    def __init__(self):
        super().__init__()

    @staticmethod
    def new_connect_rest_response():
        return ConnectResetResponse()
    
    def get_response_type(self) -> str:
        return "ConnectResetResponse"

class ClientDetectionResponse(Response):
    def __init__(self):
        super().__init__()

    @staticmethod
    def new_client_detection_response():
        return ClientDetectionResponse()
    
    def get_response_type(self) -> str:
        return "ClientDetectionResponse"

class ServerCheckResponse(Response):
    def __init__(self):
        super().__init__()
        self.connection_id: str = ""

    @staticmethod
    def new_server_check_response():
        return ServerCheckResponse()

    def get_response_type(self) -> str:
        return "ServerCheckResponse"

class InstanceResponse(Response):
    def __init__(self):
        super().__init__()

    @staticmethod
    def new_instance_response():
        return InstanceResponse()
    
    def get_response_type(self) -> str:
        return "InstanceResponse"

class BatchInstanceResponse(Response):
    def __init__(self):
        super().__init__()

    @staticmethod
    def new_batch_instance_response():
        return BatchInstanceResponse()

    def get_response_type(self) -> str:
        return "BatchInstanceResponse"

class QueryServiceResponse(Response):
    def __init__(self):
        super().__init__()
        self.service_info: Service = None
    
    @staticmethod
    def new_query_service_response():
        return QueryServiceResponse()

    def get_response_type(self) -> str:
        return "QueryServiceResponse"

# ... 其他响应类型的类实现

class SubscribeServiceResponse(Response):
    def __init__(self):
        super().__init__()
        self.service_info: Service = None

    @staticmethod
    def new_subscribe_service_response():
        return SubscribeServiceResponse()

    def get_response_type(self) -> str:
        return "SubscribeServiceResponse"
    
class ServiceListResponse(Response):
    def __init__(self):
        super().__init__()  # 调用父类Response的构造方法
        self.count = 0
        self.service_names = []

    @staticmethod
    def new_service_list_response():
        return ServiceListResponse()

    def get_response_type(self) -> str:
        return "ServiceListResponse"

# NotifySubscriberResponse继承自Response
class NotifySubscriberResponse(Response):
    def __init__(self):
        super().__init__()

    @staticmethod
    def new_notify_subscriber_response():
        return NotifySubscriberResponse()

    def get_response_type(self) -> str:
        return "NotifySubscriberResponse"

# HealthCheckResponse继承自Response
class HealthCheckResponse(Response):
    def __init__(self):
        super().__init__()

    @staticmethod
    def new_health_check_response():
        return HealthCheckResponse()

    def get_response_type(self) -> str:
        return "HealthCheckResponse"

# ErrorResponse继承自Response
class ErrorResponse(Response):
    def __init__(self):
        super().__init__()

    @staticmethod
    def new_error_response():
        return ErrorResponse()

    def get_response_type(self) -> str:
        return "ErrorResponse"

# MockResponse继承自Response
class MockResponse(Response):
    def __init__(self):
        super().__init__()
        
    @staticmethod
    def new_mock_response():
        return MockResponse()

    def get_response_type(self) -> str:
        return "MockResponse"