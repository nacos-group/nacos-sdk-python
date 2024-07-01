class Constants:
    NAMING_MODULE = "naming"

    CONFIG_MODULE = "config"

    CLIENT_VERSION = "Nacos-Python-Client:v2.0.0"

    DATA_IN_BODY_VERSION = 204

    DEFAULT_GROUP = "DEFAULT_GROUP"

    WEB_CONTEXT = "/nacos"

    APPNAME = "AppName"

    UNKNOWN_APP = "UnknownApp"

    DEFAULT_DOMAINNAME = "commonconfig.config-host.taobao.com"

    DAILY_DOMAINNAME = "commonconfig.taobao.net"

    NULL = ""

    DATAID = "dataId"

    GROUP = "group"

    DEFAULT_HEARTBEAT_INTERVAL = 5

    LAST_MODIFIED = "Last-Modified"

    ACCEPT_ENCODING = "Accept-Encoding"

    CONTENT_ENCODING = "Content-Encoding"

    PROBE_MODIFY_REQUEST = "Listening-Configs"

    PROBE_MODIFY_RESPONSE = "Probe-Modify-Response"

    PROBE_MODIFY_RESPONSE_NEW = "Probe-Modify-Response-New"

    USE_ZIP = "true"

    CONTENT_MD5 = "Content-MD5"

    CONFIG_VERSION = "Config-Version"

    CONFIG_TYPE = "Config-Type"

    ENCRYPTED_DATA_KEY = "Encrypted-Data-Key"

    IF_MODIFIED_SINCE = "If-Modified-Since"

    SPACING_INTERVAL = "client-spacing-interval"

    BASE_PATH = "/v1/cs"

    SERVICE_BASE_PATH = "/v1/ns"

    CONFIG_CONTROLLER_PATH = BASE_PATH + "/configs"

    TOKEN = "token"

    ACCESS_TOKEN = "accessToken"

    TOKEN_TTL = "tokenTtl"

    GLOBAL_ADMIN = "globalAdmin"

    USERNAME = "username"

    TOKEN_REFRESH_WINDOW = "tokenRefreshWindow"

    # second.
    ASYNC_UPDATE_ADDRESS_INTERVAL = 300

    # second.
    POLLING_INTERVAL_TIME = 15

    # millisecond.
    ONCE_TIMEOUT = 2000

    # millisecond.
    SO_TIMEOUT = 60000

    # millisecond.
    CONFIG_LONG_POLL_TIMEOUT = 30000

    # millisecond.
    MIN_CONFIG_LONG_POLL_TIMEOUT = 10000

    # millisecond.
    CONFIG_RETRY_TIME = 2000

    # Maximum number of retries.
    MAX_RETRY = 3

    # millisecond.
    RECV_WAIT_TIMEOUT = ONCE_TIMEOUT * 5

    ENCODE = "UTF-8"

    MAP_FILE = "map-file.js"

    FLOW_CONTROL_THRESHOLD = 20

    FLOW_CONTROL_SLOT = 10

    FLOW_CONTROL_INTERVAL = 1000

    DEFAULT_PROTECT_THRESHOLD = 0.0

    LINE_SEPARATOR = chr(1)

    WORD_SEPARATOR = chr(2)

    LONGPOLLING_LINE_SEPARATOR = "\r\n"

    CLIENT_APPNAME_HEADER = "Client-AppName"

    CLIENT_REQUEST_TS_HEADER = "Client-RequestTS"

    CLIENT_REQUEST_TOKEN_HEADER = "Client-RequestToken"

    ATOMIC_MAX_SIZE = 1000

    NAMING_INSTANCE_ID_SPLITTER = "#"

    NAMING_INSTANCE_ID_SEG_COUNT = 4

    NAMING_HTTP_HEADER_SPLITTER = "\\|"

    DEFAULT_CLUSTER_NAME = "DEFAULT"

    DEFAULT_HEART_BEAT_TIMEOUT = 15000

    DEFAULT_IP_DELETE_TIMEOUT = 30000

    DEFAULT_HEART_BEAT_INTERVAL = 5000

    DEFAULT_NAMESPACE_ID = "public"

    DEFAULT_USE_CLOUD_NAMESPACE_PARSING = True

    WRITE_REDIRECT_CODE = 307

    SERVICE_INFO_SPLITER = "@@"

    SERVICE_INFO_SPLIT_COUNT = 2

    NULL_STRING = "null"

    NUMBER_PATTERN = "^\\d+$"

    ANY_PATTERN = ".*"

    DEFAULT_INSTANCE_ID_GENERATOR = "simple"

    SNOWFLAKE_INSTANCE_ID_GENERATOR = "snowflake"

    HTTP_PREFIX = "http"

    ALL_PATTERN = "*"

    COLON = ":"

    LINE_BREAK = "\n"

    POUND = "#"

    VIPSERVER_TAG = "Vipserver-Tag"

    AMORY_TAG = "Amory-Tag"

    LOCATION_TAG = "Location-Tag"

    CHARSET_KEY = "charset"

    GROUP_NAME_KEY = "groupName"

    SERVICE_NAME_KEY = "serviceName"

    DEFAULT_PORT = 8848
