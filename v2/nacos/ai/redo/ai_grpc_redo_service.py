from typing import Set, cast

from v2.nacos.ai.model.a2a.a2a import AgentEndpoint
from v2.nacos.ai.redo.ai_redo_data import McpServerEndpointRedoData, \
	McpServerEndpoint, AgentEndpointRedoData
from v2.nacos.common.constants import Constants
from v2.nacos.redo.abstract_redo_service import AbstractRedoService
from v2.nacos.redo.redo_data import RedoType

MCP_SERVER_ENDPOINT_REDO_DATA_TYPE = "McpServerEndpointRedoData"
AGENT_ENDPOINT_REDO_DATA_TYPE = "AgentEndpointRedoData"


class AIGrpcRedoService(AbstractRedoService):

	def __init__(self, client_proxy):
		super().__init__(Constants.AI_MODULE)
		from v2.nacos.ai.remote.ai_grpc_client_proxy import AIGRPCClientProxy
		if not isinstance(client_proxy, AIGRPCClientProxy):
			raise TypeError(
					"client_proxy must be AIGRPCClientProxy instance")
		self.proxy = client_proxy

	async def redo_task(self):
		await self.redo_for_mcp_server_endpoints()

	async def redo_for_mcp_server_endpoints(self):
		for redo_data in await self.find_mcp_server_endpoint_redo_data():
			try:
				await self.redo_for_endpoint(redo_data)
			except Exception as e:
				self._logger.error(
						f"Redo mcp server endpoint operation {redo_data.get_redo_type()} for mcp server:{redo_data.mcp_name} failed, error:{e}"
				)

	async def redo_for_endpoint(self, redo_data: McpServerEndpointRedoData):
		redo_type = redo_data.get_redo_type()
		mcp_name = redo_data.mcp_name
		self._logger.info(
			f"Redo mcp server endpoint operation {redo_type} for {mcp_name}.")
		mcp_server_endpoint = redo_data.get()
		if redo_type is RedoType.REGISTER:
			if not self.proxy.is_enabled():
				return
			await self.proxy.do_register_mcp_server_endpoint(mcp_name,
															 mcp_server_endpoint.address,
															 mcp_server_endpoint.port,
															 mcp_server_endpoint.version)
		elif redo_type is RedoType.UNREGISTER:
			if not self.proxy.is_enabled():
				return
			await self.proxy.do_deregister_mcp_server_endpoint(mcp_name)
		elif redo_type is RedoType.REMOVE:
			await self.remove_mcp_server_endpoint_for_redo(mcp_name)
			return
	async def cached_mcp_server_endpoint_for_redo(self, mcp_name: str,
			address: str, port: int, version: str) -> None:
		redo_endpoint = McpServerEndpoint(
				address=address,
				port=port,
				version=version
		)
		endpoint_redo_data = McpServerEndpointRedoData(
				redo_endpoint, mcp_name)
		await super().cached_redo_data(mcp_name, endpoint_redo_data,
									   MCP_SERVER_ENDPOINT_REDO_DATA_TYPE)

	async def cached_agent_endpoint_for_redo(self, agent_name: str,
			agent_endpoint: AgentEndpoint) -> None:
		agent_endpoint_redo_data = AgentEndpointRedoData(
				agent_name = agent_name,
				data = agent_endpoint
		)
		await super().cached_redo_data(agent_name, agent_endpoint_redo_data,
									   AGENT_ENDPOINT_REDO_DATA_TYPE)

	async def remove_mcp_server_endpoint_for_redo(self, mcp_name: str) -> None:
		await super().remove_redo_data(mcp_name,
									   MCP_SERVER_ENDPOINT_REDO_DATA_TYPE)

	async def mcp_server_endpoint_registered(self, mcp_name: str) -> None:
		await super().data_registered(mcp_name,
									  MCP_SERVER_ENDPOINT_REDO_DATA_TYPE)

	async def agent_endpoint_registered(self, agent_name: str):
		await super().data_registered(agent_name,
									  AGENT_ENDPOINT_REDO_DATA_TYPE)

	async def mcp_server_endpoint_deregister(self, mcp_name: str) -> None:
		await super().data_deregistered(mcp_name,
										MCP_SERVER_ENDPOINT_REDO_DATA_TYPE)

	async def agent_endpoint_deregister(self, agent_name: str) -> None:
		await super().data_deregistered(agent_name,
										AGENT_ENDPOINT_REDO_DATA_TYPE)

	async def mcp_server_endpoint_deregistered(self, mcp_name: str) -> None:
		await super().data_deregistered(mcp_name,
										MCP_SERVER_ENDPOINT_REDO_DATA_TYPE)

	async def agent_endpoint_deregistered(self, agent_name: str) -> None:
		await super().data_deregistered(agent_name,
										AGENT_ENDPOINT_REDO_DATA_TYPE)

	async def is_mcp_server_endpoint_registered(self, mcp_name: str) -> bool:
		return await super().is_data_registered(mcp_name,
												MCP_SERVER_ENDPOINT_REDO_DATA_TYPE)

	async def find_mcp_server_endpoint_redo_data(self) -> Set[
		McpServerEndpointRedoData]:
		redo_data_set = await super().find_redo_data(
			MCP_SERVER_ENDPOINT_REDO_DATA_TYPE)
		return cast(Set[McpServerEndpointRedoData], redo_data_set)

	async def get_mcp_server_endpoint_by_key(self,
			mcp_name: str) -> McpServerEndpoint | None:
		redo_data = await super().get_redo_data(mcp_name,
												MCP_SERVER_ENDPOINT_REDO_DATA_TYPE)
		if redo_data is None:
			return None
		if isinstance(redo_data, McpServerEndpointRedoData):
			return redo_data.get()
		else:
			return None
