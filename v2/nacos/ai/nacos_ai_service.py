from v2.nacos import ClientConfig, NacosException, Instance
from v2.nacos.ai.model.a2a.a2a import AgentEndpoint, AgentCardDetailInfo
from v2.nacos.ai.model.ai_constant import AIConstants
from v2.nacos.ai.model.ai_param import GetMcpServerParam, ReleaseMcpServerParam, \
	RegisterMcpServerEndpointParam, SubscribeMcpServerParam, GetAgentCardParam, \
	ReleaseAgentCardParam, RegisterAgentEndpointParam, \
	DeregisterAgentEndpointParam, SubscribeAgentCardParam
from v2.nacos.ai.model.cache.agent_info_cache import AgentInfoCacheHolder
from v2.nacos.ai.model.cache.agent_subscribe_manager import \
	AgentSubscribeManager
from v2.nacos.ai.model.cache.mcp_server_info_cache import \
	McpServerInfoCacheHolder
from v2.nacos.ai.model.cache.mcp_server_subscribe_manager import \
	McpServerSubscribeManager
from v2.nacos.ai.model.mcp.mcp import McpServerDetailInfo
from v2.nacos.ai.remote.ai_grpc_client_proxy import AIGRPCClientProxy
from v2.nacos.ai.util.agent_util import validate_agent_card_field, \
	validate_agent_endpoint
from v2.nacos.common.constants import Constants
from v2.nacos.common.nacos_exception import INVALID_PARAM
from v2.nacos.nacos_client import NacosClient


class NacosAIService(NacosClient):

	def __init__(self, client_config: ClientConfig):
		super().__init__(client_config, Constants.NAMING_MODULE)
		if not client_config.namespace_id or len(
				client_config.namespace_id) == 0:
			self.namespace_id = "public"
		else:
			self.namespace_id = client_config.namespace_id
		self.mcp_server_subscribe_manager = McpServerSubscribeManager()
		self.agent_subscribe_manager = AgentSubscribeManager()

		self.grpc_client_proxy = AIGRPCClientProxy(client_config, self.http_agent)
		self.mcp_server_cache_holder = McpServerInfoCacheHolder(
			self.mcp_server_subscribe_manager,self.grpc_client_proxy)
		self.agent_info_cache_holder = AgentInfoCacheHolder(
			self.agent_subscribe_manager,self.grpc_client_proxy)

	@staticmethod
	async def create_ai_service(client_config: ClientConfig) -> 'NacosAIService':
		ai_service = NacosAIService(client_config)
		await ai_service.start()
		return ai_service

	async def start(self):
		await self.grpc_client_proxy.start(self.mcp_server_cache_holder, self.agent_info_cache_holder)


	async def get_mcp_server(self, param:GetMcpServerParam) -> McpServerDetailInfo:
		if not param.mcp_name or len(param.mcp_name) == 0:
			raise NacosException(INVALID_PARAM, "mcpName is required")

		return await self.grpc_client_proxy.query_mcp_server(param.mcp_name, param.version)

	async def release_mcp_server(self, param: ReleaseMcpServerParam) -> str:
		if not param.server_spec:
			raise NacosException(INVALID_PARAM, "serverSpec is required")
		if not param.server_spec.name or len(param.server_spec.name) == 0:
			raise NacosException(INVALID_PARAM, "serverSpec.name is required")
		if not param.server_spec.versionDetail.version or len(param.server_spec.versionDetail.version) == 0:
			raise NacosException(INVALID_PARAM, "serverSpec.versionDetail.version is required")

		if not param.mcp_endpoint_spec is None and param.mcp_endpoint_spec.type == AIConstants.MCP_ENDPOINT_TYPE_REF:
			if "namespaceId" not in param.mcp_endpoint_spec.data:
				param.mcp_endpoint_spec.data["namespaceId"] = self.namespace_id
			elif param.mcp_endpoint_spec.data["namespaceId"] != self.namespace_id:
				raise NacosException(INVALID_PARAM, "mcpEndpointSpec.data.namespaceId is not match")

		return await self.grpc_client_proxy.release_mcp_server(param.server_spec, param.tool_spec, param.mcp_endpoint_spec)

	async def register_mcp_server_endpoint(self, param: RegisterMcpServerEndpointParam):
		if not param.mcp_name or len(param.mcp_name) == 0:
			raise NacosException(INVALID_PARAM, "mcpName is required")

		instance = Instance(
				ip = param.address,
				port = param.port,
		)

		instance.check_instance_is_legal()

		return await self.grpc_client_proxy.register_mcp_server_endpoint(param.mcp_name, param.version, param.port,param.version)


	async def subscribe_mcp_server(self, param: SubscribeMcpServerParam) -> McpServerDetailInfo:
		if not param.mcp_name or len(param.mcp_name) == 0:
			raise NacosException(INVALID_PARAM, "mcpName is required")

		if not param.subscribe_callback:
			raise NacosException(INVALID_PARAM, "subscribeCallback is required")

		await self.mcp_server_subscribe_manager.register_subscriber(param.mcp_name, param.version, param.subscribe_callback)
		result = await self.grpc_client_proxy.subscribe_mcp_server(param.mcp_name, param.version)
		return result

	async def unsubscribe_mcp_server(self, param: SubscribeMcpServerParam):
		if not param.mcp_name or len(param.mcp_name) == 0:
			raise NacosException(INVALID_PARAM, "mcpName is required")
		if param.subscribe_callback is None:
			return
		await self.mcp_server_subscribe_manager.deregister_subscriber(param.mcp_name, param.version, param.subscribe_callback)
		if not self.mcp_server_subscribe_manager.is_subscribed(param.mcp_name, param.version):
			await self.grpc_client_proxy.unsubscribe_mcp_server(param.mcp_name, param.version)

	async def get_agent_card(self, param: GetAgentCardParam) -> AgentCardDetailInfo:
		if not param.agent_name or len(param.agent_name) == 0:
			raise NacosException(INVALID_PARAM, "agentName is required")
		return await self.grpc_client_proxy.get_agent_card(param.agent_name, param.registration_type, param.version)

	async def release_agent_card(self, param: ReleaseAgentCardParam):
		if not param.agent_card:
			raise NacosException(INVALID_PARAM, "agentCard can not be null")
		validate_agent_card_field("name", param.agent_card.name)
		validate_agent_card_field("version", param.agent_card.version)
		validate_agent_card_field("protocol_version", param.agent_card.protocol_version)

		if not param.registration_type or len(param.registration_type) == 0:
			param.registration_type = AIConstants.A2A_ENDPOINT_TYPE_SERVICE

		return await self.grpc_client_proxy.release_agent_card(param.agent_card, param.registration_type, param.set_as_latest)


	async def register_agent_endpoint(self, param: RegisterAgentEndpointParam):
		agent_endpoint = AgentEndpoint(
				address = param.address,
				port = param.port,
				transport=param.transport,
				path = param.path,
				support_tls = param.support_tls,
				version = param.version
		)
		if not param.agent_name or len(param.agent_name) == 0:
			raise NacosException(INVALID_PARAM, "agentName is required")
		validate_agent_endpoint(agent_endpoint)

		return await self.grpc_client_proxy.register_agent_endpoint(param.agent_name, agent_endpoint)

	async def deregister_agent_endpoint(self, param: DeregisterAgentEndpointParam):
		agent_endpoint = AgentEndpoint(
				address = param.address,
				port = param.port,
				version = param.version
		)
		if not param.agent_name or len(param.agent_name) == 0:
			raise NacosException(INVALID_PARAM, "agentName is required")
		validate_agent_endpoint(agent_endpoint)

		return await self.grpc_client_proxy.deregister_agent_endpoint(param.agent_name, agent_endpoint)

	async def subscribe_agent_card(self, param: SubscribeAgentCardParam):
		if not param.agent_name or len(param.agent_name) == 0:
			raise NacosException(INVALID_PARAM, "agentName is required")
		if not param.subscribe_callback:
			raise NacosException(INVALID_PARAM, "subscribeCallback is required")

		await self.agent_subscribe_manager.register_subscriber(
			param.agent_name, param.version, param.subscribe_callback)
		result = await self.grpc_client_proxy.subscribe_agent(
			param.agent_name, param.version)
		return result

	async def unsubscribe_agent_card(self, param: SubscribeAgentCardParam):
		if not param.agent_name or len(param.agent_name) == 0:
			raise NacosException(INVALID_PARAM, "agentName is required")
		if param.subscribe_callback is None:
			return
		await self.agent_subscribe_manager.deregister_subscriber(
			param.agent_name, param.version, param.subscribe_callback)
		if not await self.agent_subscribe_manager.is_subscribed(param.agent_name, param.version):
			await self.grpc_client_proxy.unsubscribe_agent(param.agent_name, param.version)

	async def shutdown(self):
		await self.grpc_client_proxy.close_client()
		await self.mcp_server_cache_holder.shutdown()
		await self.agent_info_cache_holder.shutdown()






