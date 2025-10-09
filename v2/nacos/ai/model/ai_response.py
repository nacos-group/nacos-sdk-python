from typing import Optional

from v2.nacos.ai.model.mcp.mcp import McpServerDetailInfo
from v2.nacos.transport.model.rpc_response import Response


class QueryMcpServerResponse(Response):
	"""Response for MCP server query requests"""
	# Detailed information about the queried MCP server
	mcpServerDetailInfo: Optional[McpServerDetailInfo] = None

	def get_response_type(self) -> str:
		"""Returns the query MCP server response type"""
		return "QueryMcpServerResponse"


class McpServerEndpointResponse(Response):
	"""Response for MCP server endpoint registration/deregistration requests"""
	# Type of endpoint operation performed (register/deregister)
	type: Optional[str] = None

	def get_response_type(self) -> str:
		"""Returns the MCP server endpoint response type"""
		return "McpServerEndpointResponse"

class ReleaseMcpServerResponse(Response):
	"""Response for MCP server release/publish requests"""
	# Unique identifier of the released MCP server
	mcpId: Optional[str] = None

	def get_response_type(self) -> str:
		"""Returns the release MCP server response type"""
		return "ReleaseMcpServerResponse"

