class UtilAndComs:
    web_context = "/nacos"

    nacos_url_base = web_context + "/v1/ns"

    nacos_url_instance = nacos_url_base + "/instance"

    nacos_url_service = nacos_url_base + "/service"

    ENCODING = "UTF-8"

    ENV_LIST_KEY = "envList"

    ALL_IPS = "000--00-ALL_IPS--00--000"

    FAILOVER_SWITCH = "00-00---000-VIPSRV_FAILOVER_SWITCH-000---00-00"

    DEFAULT_NAMESPACE_ID = "public"

    REQUEST_DOMAIN_RETRY_COUNT = 3

    DEFAULT_CLIENT_BEAT_THREAD_COUNT = 1

    DEFAULT_POLLING_THREAD_COUNT = 1

    HTTP = "http://"

    HTTPS = "https://"

