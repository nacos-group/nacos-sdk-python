import asyncio
import os
import unittest

from v2.nacos import ClientConfigBuilder
from v2.nacos.ai.model.ai_constant import AIConstants
from v2.nacos.ai.model.ai_param import GetMcpServerParam, ReleaseMcpServerParam, \
	RegisterMcpServerEndpointParam
from v2.nacos.ai.model.mcp.mcp import McpServerBasicInfo, \
	McpServerRemoteServiceConfig, McpEndpointSpce
from v2.nacos.ai.model.mcp.registry import ServerVersionDetail
from v2.nacos.ai.nacos_ai_service import NacosAIService

client_config = (ClientConfigBuilder()
                 # .access_key(os.getenv('NACOS_ACCESS_KEY'))
                 # .secret_key(os.getenv('NACOS_SECRET_KEY'))
                 .username("nacos")
                 .password("nacos")
                 .server_address(os.getenv('NACOS_SERVER_ADDR', 'localhost:8848'))
                 .log_level('INFO')
                 .build())

class TestAIClientV2(unittest.IsolatedAsyncioTestCase):

	async def test_publish_and_query_mcp_server(self):
		ai_service = await NacosAIService.create_ai_service(client_config)
		# await ai_service.release_mcp_server(ReleaseMcpServerParam(
		# 		server_spec= McpServerBasicInfo(
		# 				name="python-sdk-test-mcp-server-1",
		# 				versionDetail= ServerVersionDetail(
		# 						version="1.0.0",
		# 				),
		# 				description="python-sdk-test-mcp-server-description",
		# 				protocol="mcp-sse",
		# 				frontProtocol="mcp-sse",
		# 				remoteServerConfig = McpServerRemoteServiceConfig(
		# 						exportPath="/test/export/path",
		# 				),
		# 		),
		# 		mcp_endpoint_spec = McpEndpointSpce(
		# 				type= AIConstants.MCP_ENDPOINT_TYPE_REF,
		# 				data={
		# 						"groupName":"group1",
		# 						"serviceName":"service1",
		# 				}
		# 		),
		# ))
		#
		# await ai_service.release_mcp_server(ReleaseMcpServerParam(
		# 		server_spec=McpServerBasicInfo(
		# 				name="python-sdk-test-mcp-server-2",
		# 				versionDetail=ServerVersionDetail(
		# 						version="1.0.0",
		# 				),
		# 				description="python-sdk-test-mcp-server-description",
		# 				protocol="http",
		# 				frontProtocol="mcp-sse",
		# 				remoteServerConfig=McpServerRemoteServiceConfig(
		# 						exportPath="/test/export/path",
		# 				),
		# 		),
		# 		mcp_endpoint_spec=McpEndpointSpce(
		# 				type=AIConstants.MCP_ENDPOINT_TYPE_DIRECT,
		# 				data={
		# 					"address": "1.1.1.1",
		# 					"port": "80",
		# 				}
		# 		),
		# ))
		#
		# await ai_service.release_mcp_server(ReleaseMcpServerParam(
		# 		server_spec=McpServerBasicInfo(
		# 				name="python-sdk-test-mcp-server-2",
		# 				versionDetail=ServerVersionDetail(
		# 						version="1.0.1",
		# 						is_latest=True,
		# 				),
		# 				description="python-sdk-test-mcp-server-description",
		# 				protocol="http",
		# 				frontProtocol="mcp-sse",
		# 				remoteServerConfig=McpServerRemoteServiceConfig(
		# 						exportPath="/test/export/path",
		# 				),
		# 		),
		# 		mcp_endpoint_spec=McpEndpointSpce(
		# 				type=AIConstants.MCP_ENDPOINT_TYPE_DIRECT,
		# 				data={
		# 					"address": "1.1.1.2",
		# 					"port": "80",
		# 				}
		# 		),
		# ))
		result_1 = await ai_service.get_mcp_server(GetMcpServerParam(
				mcp_name="python-sdk-test-mcp-server-2",
				version="1.0.1",
		))

		print(result_1)


		await ai_service.register_mcp_server_endpoint(RegisterMcpServerEndpointParam(
				address="1.1.1.3",
				mcp_name="python-sdk-test-mcp-server-2",
				port=80,
				version="1.0.1",
		))

		result = await ai_service.get_mcp_server(GetMcpServerParam(
				mcp_name="python-sdk-test-mcp-server-2",
				version="1.0.1",
		))

		print(result)

		await asyncio.sleep(100)

