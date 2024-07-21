from enum import Enum

class ResponseCode(Enum):
    # 使用Enum类定义响应码
    RESPONSE_SUCCESS_CODE = 200
    RESPONSE_FAIL_CODE = 500

# 常量通常在Python中定义为全部大写
RESPONSE_SUCCESS_FIELD = "success"