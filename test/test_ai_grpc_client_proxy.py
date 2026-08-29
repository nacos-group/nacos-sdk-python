import logging
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from v2.nacos import ClientConfig
from v2.nacos.ai.model.ai_request import QueryPromptRequest
from v2.nacos.ai.model.ai_response import QueryPromptResponse
from v2.nacos.ai.remote.ai_grpc_client_proxy import AIGRPCClientProxy
from v2.nacos.common.nacos_exception import NacosException, NOT_FOUND, \
	NOT_MODIFIED, SERVER_ERROR

RESPONSE_FAILED = 500


def make_proxy(error_code: int, message: str) -> AIGRPCClientProxy:
	"""Build a proxy whose server always answers with the given error code."""
	proxy = AIGRPCClientProxy.__new__(AIGRPCClientProxy)
	proxy.rpc_client = SimpleNamespace(request=AsyncMock(
		return_value=QueryPromptResponse(resultCode=RESPONSE_FAILED,
										 errorCode=error_code,
										 message=message)))
	proxy.nacos_server_connector = SimpleNamespace(
		inject_security_info=AsyncMock())
	proxy.client_config = ClientConfig()
	proxy.app_name = "test-app"
	proxy.logger = logging.getLogger("test-ai-grpc-client-proxy")
	return proxy


class TestAIGRPCClientProxyLogging(unittest.IsolatedAsyncioTestCase):

	async def query_prompt(self, proxy: AIGRPCClientProxy) -> NacosException:
		request = QueryPromptRequest(namespaceId="public", promptKey="key")
		with self.assertRaises(NacosException) as ctx:
			await proxy.request_ai_server(request, QueryPromptResponse)
		return ctx.exception

	async def test_not_modified_response_is_not_logged_as_error(self):
		proxy = make_proxy(NOT_MODIFIED, "prompt data is up to date")

		with self.assertNoLogs(proxy.logger, level=logging.ERROR):
			exception = await self.query_prompt(proxy)

		self.assertEqual(NOT_MODIFIED, exception.error_code)

	async def test_not_found_response_is_not_logged_as_error(self):
		proxy = make_proxy(NOT_FOUND, "prompt not found")

		with self.assertNoLogs(proxy.logger, level=logging.ERROR):
			exception = await self.query_prompt(proxy)

		self.assertEqual(NOT_FOUND, exception.error_code)

	async def test_server_error_response_is_still_logged_as_error(self):
		proxy = make_proxy(SERVER_ERROR, "internal server error")

		with self.assertLogs(proxy.logger, level=logging.ERROR) as logs:
			exception = await self.query_prompt(proxy)

		self.assertEqual(SERVER_ERROR, exception.error_code)
		self.assertIn("internal server error", logs.output[0])
