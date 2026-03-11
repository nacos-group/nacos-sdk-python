import base64
import hashlib
import hmac
import json
import logging
from random import randrange
from typing import Optional

from v2.nacos.ai.model.prompt.prompt import Prompt
from v2.nacos.common.client_config import ClientConfig
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import NacosException, SERVER_ERROR, NOT_MODIFIED, NOT_FOUND
from v2.nacos.transport.http_agent import HttpAgent
from v2.nacos.transport.nacos_server_connector import NacosServerConnector
from v2.nacos.utils.common_util import get_current_time_millis
from v2.nacos.utils.md5_util import md5

PROMPT_CLIENT_PATH = "/v3/client/ai/prompt"
MAX_RETRY = 3
HTTP_NOT_MODIFIED = 304
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404


class AiHttpClientProxy:
	"""HTTP transport proxy for AI Prompt operations.

	Implements the same query_prompt interface as AIGRPCClientProxy,
	allowing NacosAIService to switch between gRPC and HTTP transport
	via the nacosAiTransportMode configuration.
	"""

	def __init__(self, client_config: ClientConfig, http_agent: HttpAgent,
			nacos_server_connector: NacosServerConnector):
		self.logger = logging.getLogger(Constants.AI_MODULE)
		self.client_config = client_config

		if not client_config.namespace_id or len(client_config.namespace_id) == 0:
			self.namespace_id = "public"
		else:
			self.namespace_id = client_config.namespace_id

		self.app_name = client_config.app_name if client_config.app_name else "unknown"
		self.http_agent = http_agent
		self.nacos_server_connector = nacos_server_connector

	async def query_prompt(self, prompt_key: str, version: Optional[str],
			label: Optional[str], md5_value: Optional[str]) -> Prompt:
		params = {
			"namespaceId": self.namespace_id,
			"promptKey": prompt_key,
		}
		if version and len(version) > 0:
			params["version"] = version
		if label and len(label) > 0:
			params["label"] = label
		if md5_value and len(md5_value) > 0:
			params["md5"] = md5_value

		response_body = await self._req_api(PROMPT_CLIENT_PATH, params)
		result = json.loads(response_body)
		data = result.get("data")
		if data is None:
			return Prompt()

		return Prompt(
			promptKey=data.get("promptKey"),
			version=data.get("version"),
			template=data.get("template"),
			md5=data.get("md5"),
		)

	async def _req_api(self, api: str, params: dict) -> str:
		server_list = self.nacos_server_connector.get_server_list()
		if not server_list:
			raise NacosException(SERVER_ERROR, "no server available")

		last_exception = None
		index = randrange(0, len(server_list))

		for i in range(max(len(server_list), MAX_RETRY)):
			server = server_list[index % len(server_list)]
			try:
				return await self._call_server(api, params, server)
			except NacosException as e:
				last_exception = e
				if e.error_code == NOT_MODIFIED or e.error_code == NOT_FOUND:
					raise
				self.logger.debug(f"Request {api} to server {server} failed: {e}")
			index = (index + 1) % len(server_list)

		self.logger.error(
			f"Request: {api} failed, servers: {server_list}, err: {last_exception}")
		raise NacosException(
			SERVER_ERROR,
			f"Failed to request API: {api} after all servers tried: {last_exception}")

	async def _call_server(self, api: str, params: dict, server: str) -> str:
		headers = await self._build_headers()

		context_path = self.client_config.context_path or Constants.WEB_CONTEXT
		tls_enabled = (self.client_config.tls_config
				and self.client_config.tls_config.enabled)
		scheme = "https" if tls_enabled else "http"
		url = f"{scheme}://{server}{context_path}{api}"

		response, err = await self.http_agent.request(
			url, "GET", headers=headers, params=params)

		if err:
			err_str = str(err)
			if str(HTTP_NOT_MODIFIED) in err_str:
				raise NacosException(NOT_MODIFIED, "not modified")
			if str(HTTP_NOT_FOUND) in err_str:
				raise NacosException(NOT_FOUND, "prompt not found")
			if str(HTTP_FORBIDDEN) in err_str:
				raise NacosException(SERVER_ERROR, "forbidden")
			raise NacosException(SERVER_ERROR, f"HTTP request failed: {err}")

		return response.decode("utf-8") if isinstance(response, bytes) else response

	async def _build_headers(self) -> dict:
		headers = {}
		await self.nacos_server_connector.inject_security_info(headers)

		now = get_current_time_millis()
		headers[Constants.CLIENT_APPNAME_HEADER] = self.app_name
		headers[Constants.CLIENT_REQUEST_TS_HEADER] = str(now)
		headers[Constants.CLIENT_REQUEST_TOKEN_HEADER] = md5(
			str(now) + self.client_config.app_key)
		headers[Constants.CHARSET_KEY] = "utf-8"
		headers['Timestamp'] = str(now)

		credentials = self.client_config.credentials_provider.get_credentials()
		if credentials.get_access_key_id() and credentials.get_access_key_secret():
			resource = self.namespace_id + "+" + "DEFAULT_GROUP"
			if resource.strip():
				sign_str = f"{resource}+{now}"
			else:
				sign_str = str(now)

			headers['Spas-AccessKey'] = credentials.get_access_key_id()
			headers['Spas-Signature'] = base64.encodebytes(
				hmac.new(
					credentials.get_access_key_secret().encode(),
					sign_str.encode(),
					digestmod=hashlib.sha1).digest()).decode().strip()
			if credentials.get_security_token():
				headers['Spas-SecurityToken'] = credentials.get_security_token()

		return headers

	async def close(self):
		pass
