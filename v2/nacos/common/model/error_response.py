from v2.nacos.common.model.response import Response
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException

class ErrorResponse(Response):
    
    @classmethod
    def build(cls, error_code, msg):
        response = cls()
        response.result_code = Constants.RESPONSE_CODE_FAIL #500
        response.error_code = error_code
        response.message = msg
        return response

    @classmethod
    def build_from_exception(cls, exception):
        error_code = Constants.RESPONSE_CODE_FAIL
        if isinstance(exception, NacosException):
            error_code = exception.error_code
        elif isinstance(exception, NacosRuntimeException):
            error_code = exception.error_code
        response = cls()
        response.result_code = Constants.RESPONSE_CODE_FAIL #500
        response.error_code = error_code
        response.message = str(exception)
        return response