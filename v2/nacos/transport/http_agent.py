import ssl
from http import HTTPStatus
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from v2.nacos.common.client_config import TLSConfig

HTTP_STATUS_SUCCESS = 200


class HttpAgent:
    def __init__(self, logger, tls_config: TLSConfig, default_timeout):
        self.logger = logger
        self.tls_config = tls_config
        self.default_timeout = default_timeout

    def create_ssl_context(self):
        if self.tls_config is None or not self.tls_config.enabled:
            # 如果未开启tls，则无需创建ssl context
            return None

        ctx = ssl.create_default_context(
            cafile=self.tls_config.ca_file) if self.tls_config.ca_file else ssl.create_default_context()

        if self.tls_config.cert_file and self.tls_config.key_file:
            ctx.load_cert_chain(certfile=self.tls_config.cert_file, keyfile=self.tls_config.key_file)

        return ctx

    def request(self, url, method, headers=None, params=None, data=None):
        if not headers:
            headers = {}

        if params:
            url += '?' + urlencode(params)

        data = urlencode(data).encode() if data else None

        self.logger.debug(
            f"[http-request] url: {url}, headers: {headers}, params: {params}, data: {data}, timeout: {self.default_timeout}")

        try:
            if not url.startswith("http"):
                url = f"http://{url}"

            ctx = self.create_ssl_context()

            request = Request(url=url, data=data, headers=headers, method=method)

            response = urlopen(request, timeout=self.default_timeout, context=ctx)

            return response.read(), None
        except HTTPError as e:
            if e.code in [HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.BAD_GATEWAY,
                          HTTPStatus.SERVICE_UNAVAILABLE]:
                self.logger.debug(f"[http-request] http error msg : {e.reason}")
            return None, e
        except URLError as e:
            self.logger.debug(f"[http-request] url error msg : {e.reason}")
            return None, e
