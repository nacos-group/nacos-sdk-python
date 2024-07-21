import json
from typing import Any, Callable, Optional

# 假设IResponse接口已经被定义
class IResponse:
    def is_success(self) -> bool:
        pass

    def set_success(self, success: bool):
        pass

    def get_result_code(self) -> int:
        pass

# 假设Response类已经被定义并实现了IResponse接口
class Response:
    def __init__(self):
        self.success: bool = False
        self.result_code: int = 0

    def is_success(self) -> bool:
        return self.success

    def set_success(self, success: bool):
        self.success = success

    def get_result_code(self) -> int:
        return self.result_code

# 假设ResponseSuccessField常量已经被定义
RESPONSE_SUCCESS_FIELD = "success"

def inner_response_json_unmarshal(response_body: bytes, response_func: Callable[[], IResponse]) -> tuple[Optional[IResponse], Exception]:
    response = response_func()
    try:
        json.loads(response_body)  # 尝试解析JSON以触发解码错误
        # Python json模块的loads函数不会修改response对象，需要自定义解析逻辑
    except json.JSONDecodeError as err:
        return None, err

    if not response.is_success():
        temp_field_map = {}  # 用于临时存储解析的JSON数据
        try:
            temp_field_map = json.loads(response_body)  # 重新解析为字典
        except json.JSONDecodeError as err:
            return response, err

        if RESPONSE_SUCCESS_FIELD not in temp_field_map:
            response.set_success(response.get_result_code() == ResponseCode.RESPONSE_SUCCESS_CODE.value)

    return response, None

# 使用示例
# 假设我们有一个JSON响应体和对应的response对象创建函数
response_body = b'{"success": true, "resultCode": 200}'
response, error = inner_response_json_unmarshal(response_body, Response)
if error:
    print("An error occurred:", error)
else:
    print("Response success:", response.is_success())