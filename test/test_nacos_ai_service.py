import unittest

from v2.nacos.ai.model.ai_param import GetAgentCardParam
from v2.nacos.ai.nacos_ai_service import NacosAIService


class RecordingAgentCardProxy:
	async def get_agent_card(self, agent_name, version, registration_type):
		return agent_name, version, registration_type


class TestNacosAIService(unittest.IsolatedAsyncioTestCase):
	async def test_get_agent_card_preserves_version_and_registration_type(self):
		service = object.__new__(NacosAIService)
		service.grpc_client_proxy = RecordingAgentCardProxy()

		result = await service.get_agent_card(GetAgentCardParam(
			agent_name="demo-agent",
			version="1.2.3",
			registration_type="url",
		))

		self.assertEqual(("demo-agent", "1.2.3", "url"), result)
