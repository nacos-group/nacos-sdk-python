import ssl
from http import HTTPStatus
from urllib.parse import urlencode
import aiohttp

from v2.nacos.common.client_config import TLSConfig

HTTP_STATUS_SUCCESS = 200


class HttpAgent:
    def __init__(self, logger, tls_config: TLSConfig, default_timeout):
        self.logger = logger
        self.tls_config = tls_config
        self.default_timeout = default_timeout

        self.ssl_context = None
        if tls_config and tls_config.enabled:
            ctx = ssl.create_default_context(
                cafile=tls_config.ca_file) if tls_config.ca_file else ssl.create_default_context()

            if self.tls_config.cert_file and self.tls_config.key_file:
                ctx.load_cert_chain(certfile=self.tls_config.cert_file, keyfile=self.tls_config.key_file)
            self.ssl_context = ctx

    async def request(self, url: str, method: str, headers: dict = None, params: dict = None, data: dict = None):
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

            connector = aiohttp.TCPConnector(ssl=self.ssl_context) if self.ssl_context else aiohttp.TCPConnector()
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.default_timeout),
                                             connector=connector) as session:
                async with session.request(method, url, headers=headers, data=data) as response:
                    if response.status == HTTPStatus.OK:
                        return await response.read(), None
                    else:
                        error_msg = f"HTTP error: {response.status} - {response.reason}"
                        self.logger.debug(f"[http-request] {error_msg}")
                        return None, error_msg

        except aiohttp.ClientError as e:
            self.logger.warning(f"[http-request] client error: {e}")
            return None, e
        except Exception as e:
            self.logger.warning(f"[http-request] unexpected error: {e}")
            return None, e
