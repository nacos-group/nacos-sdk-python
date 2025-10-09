import asyncio
import os
import unittest
from datetime import datetime

from v2.nacos import ClientConfigBuilder
from v2.nacos.ai.model.ai_constant import AIConstants
from v2.nacos.ai.model.ai_param import GetMcpServerParam, ReleaseMcpServerParam, \
	RegisterMcpServerEndpointParam, SubscribeMcpServerParam
from v2.nacos.ai.model.mcp.mcp import McpServerBasicInfo, \
	McpServerRemoteServiceConfig, McpEndpointSpce, McpServerDetailInfo
from v2.nacos.ai.model.mcp.registry import ServerVersionDetail
from v2.nacos.ai.nacos_ai_service import NacosAIService

client_config = (ClientConfigBuilder()
                 .username("nacos")
                 .password("nacos")
                 .server_address(os.getenv('NACOS_SERVER_ADDR', 'localhost:8848'))
                 .log_level('INFO')
                 .build())

class TestAIClientV2(unittest.IsolatedAsyncioTestCase):

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

