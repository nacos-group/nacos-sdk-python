from enum import Enum
import time


# 定义枚举类型
class KMSVersion(Enum):
    KMSv1 = "KMSv1"
    KMSv3 = "KMSv3"
    DEFAULT_KMS_VERSION = ""  # 适配原始版本
    UNKNOWN_KMS_VERSION = "UNKNOWN_KMS_VERSION"


class Const:
    # 常量定义
    KEY_USERNAME = "username"
    KEY_PASSWORD = "password"
    KEY_ENDPOINT = "endpoint"
    KEY_NAME_SPACE = "namespace"
    KEY_ACCESS_KEY = "accessKey"
    KEY_SECRET_KEY = "secretKey"
    # ... 其他常量定义

    WEB_CONTEXT = "/nacos"
    CONFIG_BASE_PATH = "/v1/cs"
    CONFIG_PATH = CONFIG_BASE_PATH + "/configs"
    # ... 其他路径定义

    SPLIT_CONFIG = chr(1)
    SPLIT_CONFIG_INNER = chr(2)
    # ... 其他字符常量定义

    KEY_LISTEN_CONFIGS = "Listening-Configs"
    # ... 其他键定义

    DEFAULT_CONTEXT_PATH = "/nacos"
    CLIENT_VERSION = "Nacos-Go-Client:v2.2.6"
    REQUEST_DOMAIN_RETRY_TIME = 3
    # ... 其他数字常量定义

    SERVICE_INFO_SPLITER = "@@"
    CONFIG_INFO_SPLITER = "@@"
    # ... 其他字符串分隔符定义

    DEFAULT_NAMESPACE_ID = "public"
    DEFAULT_GROUP = "DEFAULT_GROUP"
    # ... 其他默认值定义

    NAMING_INSTANCE_ID_SPLITTER = "#"
    DefaultClientErrorCode = "SDK.NacosError"
    # ... 其他错误代码定义

    DEFAULT_SERVER_SCHEME = "http"
    HTTPS_SERVER_SCHEME = "https"
    # ... 其他协议定义

    LABEL_SOURCE = "source"
    # ... 其他标签定义

    RESPONSE_CODE_SUCCESS = 200
    UN_REGISTER = 301
    # ... 其他响应代码定义

    KEEP_ALIVE_TIME = 5
    DEFAULT_TIMEOUT_MILLS = 3000
    # ... 其他时间相关定义

    ALL_SYNC_INTERNAL = 5 * time.Minute
    # ... 其他时间间隔定义

    CLIENT_APPNAME_HEADER = "Client-AppName"
    # ... 其他HTTP头定义

    HTTPS_SERVER_PORT = 443
    GRPC = "grpc"
    # ... 其他服务定义

    RpcPortOffset = 1000
    MSE_KMSv1_DEFAULT_KEY_ID = "alias/acs/mse"
