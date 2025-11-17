import base64
import hashlib
import hmac
import logging
import uuid
from typing import Optional

from a2a.types import AgentCard

from v2.nacos import ClientConfig, NacosException
from v2.nacos.ai.model.a2a.a2a import AgentCardDetailInfo, AgentEndpoint
from v2.nacos.ai.model.ai_constant import AIConstants
from v2.nacos.ai.model.ai_request import AbstractAIRequest, AbstractMcpRequest, \
	QueryMcpServerRequest, ReleaseMcpServerRequest, McpServerEndpointRequest, \
	QueryAgentCardRequest, ReleaseAgentCardRequest, AgentEndpointRequest
from v2.nacos.ai.model.ai_response import QueryMcpServerResponse, \
	ReleaseMcpServerResponse, McpServerEndpointResponse, QueryAgentCardResponse, \
	ReleaseAgentCardResponse, AgentEndpointResponse
from v2.nacos.ai.model.cache.agent_info_cache import AgentInfoCacheHolder
from v2.nacos.ai.model.cache.mcp_server_info_cache import \
	McpServerInfoCacheHolder
from v2.nacos.ai.model.mcp.mcp import McpServerBasicInfo, McpToolSpecification, \
	McpEndpointSpce, McpServerDetailInfo
from v2.nacos.ai.redo.ai_grpc_redo_service import AIGrpcRedoService
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import SERVER_ERROR, SERVER_NOT_IMPLEMENTED
from v2.nacos.transport.ability import AbilityKey, AbilityStatus
from v2.nacos.transport.http_agent import HttpAgent
from v2.nacos.transport.nacos_server_connector import NacosServerConnector
from v2.nacos.transport.rpc_client import ConnectionType
from v2.nacos.transport.rpc_client_factory import RpcClientFactory
from v2.nacos.utils.common_util import get_current_time_millis
from v2.nacos.utils.md5_util import md5


class AIGRPCClientProxy:

	def __init__(self,
			client_config: ClientConfig,
			http_client: HttpAgent):
		self.cache_holder : Optional[McpServerInfoCacheHolder] = None
		self.agent_cache_holder : Optional[AgentInfoCacheHolder] = None
		self.logger = logging.getLogger(Constants.AI_MODULE)
		self.client_config = client_config
		self.uuid = uuid.uuid4()

		self.rpc_client = None
		self.app_name = self.client_config.app_name if self.client_config.app_name else "unknown"
		if not client_config.namespace_id or len(client_config.namespace_id) == 0 :
			self.namespace_id = "public"
		else:
			self.namespace_id = client_config.namespace_id

		self.nacos_server_connector = NacosServerConnector(self.logger,
														   client_config,
														   http_client)

		self.redo_service = AIGrpcRedoService(self)

	async def start(self, mcp_server_cache_holder: McpServerInfoCacheHolder, agent_info_cache_holder : AgentInfoCacheHolder):
		self.cache_holder = mcp_server_cache_holder
		self.agent_cache_holder = agent_info_cache_holder

		await self.nacos_server_connector.init()
		labels = {Constants.LABEL_SOURCE: Constants.LABEL_SOURCE_SDK,
				  Constants.LABEL_MODULE: Constants.AI_MODULE}
		self.rpc_client = await RpcClientFactory(self.logger).create_client(
			str(self.uuid), ConnectionType.GRPC, labels,
			self.client_config,
			self.nacos_server_connector)
		await self.rpc_client.register_connection_listener(self.redo_service)

		await self.rpc_client.start()

	async def request_ai_server(self, request: AbstractAIRequest, response_class):
		try:
			if not isinstance(request, AbstractAIRequest):
				raise NacosException(f"Unknown AI Request Type:{request.get_request_type()}")
			await self.nacos_server_connector.inject_security_info(
				request.get_headers())

			now = get_current_time_millis()
			request.put_all_headers({
				Constants.CLIENT_APPNAME_HEADER: self.app_name,
				Constants.CLIENT_REQUEST_TS_HEADER: str(now),
				Constants.CLIENT_REQUEST_TOKEN_HEADER: md5(
					str(now) + self.client_config.app_key),
				Constants.CHARSET_KEY: "utf-8",
				'Timestamp': str(now),
			})

			credentials = self.client_config.credentials_provider.get_credentials()
			if credentials.get_access_key_id() and credentials.get_access_key_secret():
				resource = request.namespaceId + "+" + "DEFAULT_GROUP"
				if resource.strip():
					sign_str = f"{resource}+{now}"
				else:
					sign_str = str(now)

				request.put_all_headers({
					'Spas-AccessKey': credentials.get_access_key_id(),
					'Spas-Signature': base64.encodebytes(
							hmac.new(
								credentials.get_access_key_secret().encode(),
								sign_str.encode(),
								digestmod=hashlib.sha1).digest()).decode().strip(),
				})
				if credentials.get_security_token():
					request.put_header("Spas-SecurityToken",
									   credentials.get_security_token())

			response = await self.rpc_client.request(request,
												self.client_config.grpc_config.grpc_timeout)
			if response.get_result_code() != 200:
				raise NacosException(response.get_error_code(),
									 response.get_message())
			if issubclass(response.__class__, response_class):
				return response
			else:
				raise NacosException(SERVER_ERROR,
									 " Server return invalid response")
		except NacosException as e:
			self.logger.error(
				"failed to invoke nacos config server : " + str(e))
			raise e
		except Exception as e:
			self.logger.error(
				"failed to invoke nacos config server : " + str(e))
			raise NacosException(SERVER_ERROR,
								 "Request nacos config server failed: " + str(
									 e))

	def is_ability_supported_by_server(self,ability_key:AbilityKey) -> bool:
		return self.rpc_client.get_connection_ability(ability_key) == AbilityStatus.SUPPORTED


	async def query_mcp_server(self, mcp_name: str, version: str) -> McpServerDetailInfo:
		if not self.is_ability_supported_by_server(AbilityKey.SERVER_MCP_REGISTRY):
			raise NacosException(SERVER_NOT_IMPLEMENTED,"Request Nacos server version is too low, not support mcp registry feature.")

		request = QueryMcpServerRequest(
				namespaceId=self.namespace_id,
				mcpName=mcp_name,
				version=version,
		)

		response = await self.request_ai_server(request, QueryMcpServerResponse)
		return response.mcpServerDetailInfo

	async def release_mcp_server(self,server_spec: McpServerBasicInfo, tool_spec: McpToolSpecification, endpoint_spec: McpEndpointSpce):
		self.logger.info(
			f"[{self.uuid}] release mcp server: {server_spec.name}, version {server_spec.versionDetail.version}")
		if not self.is_ability_supported_by_server(AbilityKey.SERVER_MCP_REGISTRY):
			raise NacosException(SERVER_NOT_IMPLEMENTED,"Request Nacos server version is too low, not support mcp registry feature.")

		request = ReleaseMcpServerRequest(
				namespaceId=self.namespace_id,
				mcpName=server_spec.name,
				serverSpecification=server_spec,
				toolSpecification=tool_spec,
				endpointSpecification=endpoint_spec
		)

		response = await self.request_ai_server(request, ReleaseMcpServerResponse)
		return response.mcpId

	async def register_mcp_server_endpoint(self,mcp_name:str, address: str, port: int, version:str):
		self.logger.info(f"[{self.uuid}] register mcp server endpoint: {mcp_name}, address {address}, port {port}, version {version}")
		if not self.is_ability_supported_by_server(AbilityKey.SERVER_MCP_REGISTRY):
			raise NacosException(SERVER_NOT_IMPLEMENTED,"Request Nacos server version is too low, not support mcp registry feature.")

		await self.do_register_mcp_server_endpoint(mcp_name, address, port, version)

	async def do_register_mcp_server_endpoint(self,mcp_name:str, address: str, port: int, version:str):
		await self.redo_service.cached_mcp_server_endpoint_for_redo(mcp_name, address, port, version)
		request = McpServerEndpointRequest(
				namespaceId= self.namespace_id,
				mcpName=mcp_name,
				address=address,
				port=port,
				version=version,
				type=AIConstants.REGISTER_ENDPOINT
		)
		await self.request_ai_server(request, McpServerEndpointResponse)
		await self.redo_service.mcp_server_endpoint_registered(mcp_name)

	async def deregister_mcp_server_endpoint(self,mcp_name:str, address: str, port: int):
		self.logger.info(f"[{self.uuid}] deregister mcp server endpoint: {mcp_name}, address {address}, port {port}")
		if not self.is_ability_supported_by_server(AbilityKey.SERVER_MCP_REGISTRY):
			raise NacosException(SERVER_NOT_IMPLEMENTED,"Request Nacos server version is too low, not support mcp registry feature.")
		await self.do_deregister_mcp_server_endpoint(mcp_name, address, port)

	async def do_deregister_mcp_server_endpoint(self,mcp_name:str, address: str, port: int):
		await self.redo_service.mcp_server_endpoint_deregister(mcp_name)
		request = McpServerEndpointRequest(
				namespaceId= self.namespace_id,
				mcpName=mcp_name,
				address=address,
				port=port,
				type=AIConstants.DE_REGISTER_ENDPOINT
		)
		await self.request_ai_server(request, McpServerEndpointResponse)
		await self.redo_service.mcp_server_endpoint_deregistered(mcp_name)

	async def subscribe_mcp_server(self, mcp_name:str, version:str) -> McpServerDetailInfo:
		if not self.is_ability_supported_by_server(AbilityKey.SERVER_MCP_REGISTRY):
			raise NacosException(SERVER_NOT_IMPLEMENTED,"Request Nacos server version is too low, not support mcp registry feature.")

		mcp_detail_info = await self.cache_holder.get_mcp_server(mcp_name, version)
		if mcp_detail_info is None:
			mcp_detail_info = await self.query_mcp_server(mcp_name, version)
			await self.cache_holder.process_mcp_server_detail_info(mcp_detail_info)
			await self.cache_holder.add_mcp_server_update_task(mcp_name, version)

		return mcp_detail_info

	async def unsubscribe_mcp_server(self, mcp_name:str, version:str):
		if not self.is_ability_supported_by_server(AbilityKey.SERVER_MCP_REGISTRY):
			raise NacosException(SERVER_NOT_IMPLEMENTED,"Request Nacos server version is too low, not support mcp registry feature.")
		await self.cache_holder.remove_mcp_server_update_task(mcp_name, version)

	async def get_agent_card(self, agent_name: str, version: str, registration_type: str) -> AgentCardDetailInfo:
		if not self.is_ability_supported_by_server(AbilityKey.SERVER_AGENT_REGISTRY):
			raise NacosException(SERVER_NOT_IMPLEMENTED,"Request Nacos server version is too low, not support agent registry feature.")
		request = QueryAgentCardRequest(
				namespaceId=self.namespace_id,
				agentName=agent_name,
				version=version,
				registrationType=registration_type
		)
		response = await self.request_ai_server(request, QueryAgentCardResponse)
		return response.agentCardDetailInfo

	async def release_agent_card(self, agent_card: AgentCard, registration_type: str, set_as_latest: bool):
		self.logger.info(f"[{self.uuid}] release agent card: {agent_card.name}, version {agent_card.version}")
		if not self.is_ability_supported_by_server(AbilityKey.SERVER_AGENT_REGISTRY):
			raise NacosException(SERVER_NOT_IMPLEMENTED,"Request Nacos server version is too low, not support agent registry feature.")
		request = ReleaseAgentCardRequest(
				namespaceId=self.namespace_id,
				agentName= agent_card.name,
				registrationType= registration_type,
				agentCard=agent_card,
				setAsLatest=set_as_latest
		)
		await self.request_ai_server(request, ReleaseAgentCardResponse)

	async def register_agent_endpoint(self, agent_name: str, agent_endpoint: AgentEndpoint):
		self.logger.info(f"[{self.uuid}] register agent endpoint: {agent_endpoint} into agent {agent_name}")
		if not self.is_ability_supported_by_server(AbilityKey.SERVER_AGENT_REGISTRY):
			raise NacosException(SERVER_NOT_IMPLEMENTED,"Request Nacos server version is too low, not support agent registry feature.")
		await self.do_register_agent_endpoint(agent_name, agent_endpoint)

	async def do_register_agent_endpoint(self, agent_name: str, agent_endpoint: AgentEndpoint):
		await self.redo_service.cached_agent_endpoint_for_redo(agent_name,
															   agent_endpoint)
		agent_endpoint_request = AgentEndpointRequest(
				namespaceId=self.namespace_id,
				agentName=agent_name,
				type=AIConstants.REGISTER_ENDPOINT,
				endpoint=agent_endpoint
		)
		await self.request_ai_server(agent_endpoint_request, AgentEndpointResponse)
		await self.redo_service.agent_endpoint_registered(agent_name)


	async def deregister_agent_endpoint(self, agent_name: str, agent_endpoint: AgentEndpoint):
		self.logger.info(f"[{self.uuid}] deregister agent endpoint: {agent_endpoint} from agent {agent_name}")
		if not self.is_ability_supported_by_server(AbilityKey.SERVER_AGENT_REGISTRY):
			raise NacosException(SERVER_NOT_IMPLEMENTED,"Request Nacos server version is too low, not support agent registry feature.")
		await self.do_deregister_agent_endpoint(agent_name, agent_endpoint)

	async def do_deregister_agent_endpoint(self, agent_name: str, agent_endpoint: AgentEndpoint):
		await self.redo_service.agent_endpoint_deregister(agent_name)
		agent_endpoint_request = AgentEndpointRequest(
				namespaceId=self.namespace_id,
				agentName=agent_name,
				type=AIConstants.DE_REGISTER_ENDPOINT,
				endpoint=agent_endpoint
		)
		await self.request_ai_server(agent_endpoint_request, AgentEndpointResponse)
		await self.redo_service.agent_endpoint_deregistered(agent_name)

	async def subscribe_agent(self, agent_name:str, version:str) -> AgentCardDetailInfo:
		if not self.is_ability_supported_by_server(AbilityKey.SERVER_AGENT_REGISTRY):
			raise NacosException(SERVER_NOT_IMPLEMENTED,"Request Nacos server version is too low, not support agent registry feature.")
		agent_card_detail_info = await self.agent_cache_holder.get_agent_card(agent_name, version)
		if agent_card_detail_info is None:
			agent_card_detail_info = await self.get_agent_card(agent_name, version, "")
			await self.agent_cache_holder.process_agent_card_detail_info(agent_card_detail_info)
			await self.agent_cache_holder.add_agent_update_task(agent_name, version)

		return agent_card_detail_info

	async def unsubscribe_agent(self, agent_name:str, version:str):
		if not self.is_ability_supported_by_server(AbilityKey.SERVER_AGENT_REGISTRY):
			raise NacosException(SERVER_NOT_IMPLEMENTED,"Request Nacos server version is too low, not support agent registry feature.")
		await self.agent_cache_holder.remove_agent_update_task(agent_name, version)


	async def close_client(self):
		self.logger.info("close Nacos python ai grpc client...")
		await self.rpc_client.shutdown()

	async def is_enabled(self):
		return self.rpc_client.is_running()