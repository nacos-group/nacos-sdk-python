import asyncio
import os
import unittest
from datetime import datetime

from a2a.types import AgentCard, AgentSkill, AgentCapabilities

from v2.nacos import ClientConfigBuilder
from v2.nacos.ai.model.a2a.a2a import AgentCardDetailInfo
from v2.nacos.ai.model.ai_constant import AIConstants
from v2.nacos.ai.model.ai_param import GetMcpServerParam, ReleaseMcpServerParam, \
	RegisterMcpServerEndpointParam, SubscribeMcpServerParam, \
	ReleaseAgentCardParam, GetAgentCardParam, RegisterAgentEndpointParam, \
	SubscribeAgentCardParam, DeregisterAgentEndpointParam
from v2.nacos.ai.model.mcp.mcp import McpServerBasicInfo, \
	McpServerRemoteServiceConfig, McpEndpointSpce, McpServerDetailInfo
from v2.nacos.ai.model.mcp.registry import ServerVersionDetail
from v2.nacos.ai.nacos_ai_service import NacosAIService

client_config = (ClientConfigBuilder()
                 .server_address(os.getenv('NACOS_SERVER_ADDR', 'localhost:8848'))
                 .log_level('INFO')
                 .build())

class TestAIClientV2(unittest.IsolatedAsyncioTestCase):

	async def test_agent(self):
		capabilities = AgentCapabilities(
				streaming=False,
				push_notifications=False,
		)

		# Define agent skills
		skill = AgentSkill(
				id="dialog",
				name="Natural Language Dialog Skill",
				description="Enables natural language conversation and dialogue "
							"with users",
				tags=["natural language", "dialog", "conversation"],
				examples=[
					"Hello, how are you?",
					"Can you help me with something?",
				],
		)

		agent_card =  AgentCard(
				capabilities=capabilities,
				skills=[skill],
				name="nacos-test-agent",
				description="This is a test a2a agent",
				default_input_modes=["text"],
				default_output_modes=["text"],
				url="http://localhost:8848",
				version="1.0.0",
		)
		ai_service = await NacosAIService.create_ai_service(client_config)

		await ai_service.release_agent_card(ReleaseAgentCardParam(
				agent_card=agent_card,
				set_as_latest=True,
		))

		await asyncio.sleep(3)


		result_1 = await ai_service.get_agent_card(GetAgentCardParam(
				agent_name="nacos-test-agent",
				version="1.0.0",
		))

		self.assertEqual(result_1.name, "nacos-test-agent")
		self.assertEqual(result_1.description, "This is a test a2a agent")
		self.assertEqual(result_1.default_input_modes, ["text"])

		async def callback (agent_name, agent_card_detail_info:AgentCardDetailInfo):
			print("------------------- Agent Card Changed---------------------")
			print(agent_name)
			print(agent_card_detail_info.model_dump_json(indent=2))

		await ai_service.subscribe_agent_card(SubscribeAgentCardParam(
				agent_name="nacos-test-agent",
				version="1.0.0",
				subscribe_callback=callback
		))

		await asyncio.sleep(15)

		await ai_service.register_agent_endpoint(RegisterAgentEndpointParam(
				agent_name="nacos-test-agent",
				address="1.1.1.1",
				port=80,
				support_tls=True,
				version="1.0.0",
		))
		print(
			"------------------- Register Agent Endpoint 1---------------------")
		await asyncio.sleep(15)


		ai_service_2 = await NacosAIService.create_ai_service(client_config)

		await ai_service_2.register_agent_endpoint(RegisterAgentEndpointParam(
				agent_name="nacos-test-agent",
				address="1.1.1.2",
				port=80,
				support_tls=False,
				version="1.0.0",
		))
		print(
				"------------------- Register Agent Endpoint 2---------------------")
		await asyncio.sleep(15)

		await ai_service.deregister_agent_endpoint(DeregisterAgentEndpointParam(
				agent_name="nacos-test-agent",
				address="1.1.1.1",
				port=80,
				version="1.0.0",
		))

		print(
				"------------------- Deregister Agent Endpoint 1---------------------")
		await asyncio.sleep(15)

		await ai_service.unsubscribe_agent_card(SubscribeAgentCardParam(
				agent_name="nacos-test-agent",
				version="1.0.0",
				subscribe_callback=callback
		))

		print(
				"------------------- Unsubscribe Agent ---------------------")

		await asyncio.sleep(15)

		await ai_service_2.deregister_agent_endpoint(DeregisterAgentEndpointParam(
				agent_name="nacos-test-agent",
				address="1.1.1.2",
				port=80,
				version="1.0.0",
		))

		print(
				"------------------- Deregister Agent Endpoint 2---------------------")

		await asyncio.sleep(100)




	async def test_publish_and_query_mcp_server(self):
		ai_service = await NacosAIService.create_ai_service(client_config)
		await ai_service.release_mcp_server(ReleaseMcpServerParam(
				server_spec= McpServerBasicInfo(
						name="python-sdk-test-mcp-server-1",
						versionDetail= ServerVersionDetail(
								version="1.0.0",
						),
						description="python-sdk-test-mcp-server-description",
						protocol="mcp-sse",
						frontProtocol="mcp-sse",
						remoteServerConfig = McpServerRemoteServiceConfig(
								exportPath="/test/export/path",
						),
				),
				mcp_endpoint_spec = McpEndpointSpce(
						type= AIConstants.MCP_ENDPOINT_TYPE_REF,
						data={
								"groupName":"group1",
								"serviceName":"service1",
						}
				),
		))

		result_1 = await ai_service.get_mcp_server(GetMcpServerParam(
				mcp_name="python-sdk-test-mcp-server-1",
				version="1.0.0",
		))
		print("------------------- Get MCP Server ---------------------")
		print(result_1.model_dump_json(indent=2))
		async def callback (mcp_id, namespace_id, mcp_name, mcp_server_detail_info:McpServerDetailInfo):
			print("------------------- MCP Server Changed---------------------")
			print(mcp_id)
			print(namespace_id)
			print(mcp_name)
			print(mcp_server_detail_info.model_dump_json(indent=2))
			timestamp = datetime.now().timestamp()
			print(f"time: {timestamp}")
			print("------------------- Callback Finished---------------------")

		await ai_service.subscribe_mcp_server(SubscribeMcpServerParam(

				mcp_name="python-sdk-test-mcp-server-1",
				version="1.0.0",
				subscribe_callback=callback
		))

		await asyncio.sleep(1)

		await ai_service.register_mcp_server_endpoint(
				RegisterMcpServerEndpointParam(
						mcp_name="python-sdk-test-mcp-server-1",
						version="1.0.0",
						address="1.1.1.1",
						port=80,
				))
		print("------------------- Register MCP Server ---------------------")

		await asyncio.sleep(100)

