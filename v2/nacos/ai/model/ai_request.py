from abc import ABC
from typing import Optional

from a2a.types import AgentCard

from v2.nacos.ai.model.a2a.a2a import AgentEndpoint
from v2.nacos.ai.model.ai_constant import AIConstants
from v2.nacos.ai.model.mcp.mcp import McpServerBasicInfo, McpToolSpecification, \
	McpEndpointSpce
from v2.nacos.common.constants import Constants
from v2.nacos.transport.model.rpc_request import Request


class AbstractAIRequest(Request, ABC):
	"""Abstract base class for all AI module requests"""

	def get_module(self) -> str:
		"""Returns the AI module identifier"""
		return Constants.AI_MODULE


class AbstractAgentRequest(AbstractAIRequest, ABC):
	"""Abstract base class for Agent requests"""
	# Namespace ID for isolating agents between different tenants
	namespaceId: Optional[str] = None
	# Name of the agent
	agentName: Optional[str] = None

	def get_request_type(self) -> str:
		"""Returns the request type, must be implemented by subclasses"""
		raise NotImplementedError("Subclasses should implement this method.")


AGENT_ENDPOINT_REQUEST_TYPE = "AgentEndpointRequest"
QUERY_AGENT_CARD_REQUEST_TYPE = "QueryAgentCardRequest"
RELEASE_AGENT_CARD_REQUEST_TYPE = "ReleaseAgentCardRequest"


class AgentEndpointRequest(AbstractAgentRequest):
	"""Request for registering or deregistering an Agent endpoint"""
	endpoint: Optional[AgentEndpoint] = None
	# Operation type: REGISTER_ENDPOINT or DE_REGISTER_ENDPOINT from AIConstants
	type: Optional[str] = None

	def get_request_type(self) -> str:
		"""Returns the agent endpoint request type"""
		return AGENT_ENDPOINT_REQUEST_TYPE


class QueryAgentCardRequest(AbstractAgentRequest):
	"""Request for querying agent card details"""
	# Version of the agent card to query
	version: Optional[str] = None
	# A2A_ENDPOINT_TYPE_URL or A2A_ENDPOINT_TYPE_SERVICE from AIConstants
	registrationType: Optional[str] = None

	def get_request_type(self) -> str:
		"""Returns the query agent card request type"""
		return QUERY_AGENT_CARD_REQUEST_TYPE


class ReleaseAgentCardRequest(AbstractAgentRequest):
	"""Request for releasing/publishing a new Agent to the registry"""
	# Agent card information to be released
	agentCard: Optional[AgentCard] = None
	# A2A_ENDPOINT_TYPE_URL or A2A_ENDPOINT_TYPE_SERVICE from AIConstants
	registrationType: Optional[str] = AIConstants.A2A_ENDPOINT_TYPE_SERVICE
	# Whether to set this version as the latest
	setAsLatest: Optional[bool] = False

	def get_request_type(self) -> str:
		"""Returns the release agent card request type"""
		return RELEASE_AGENT_CARD_REQUEST_TYPE


class AbstractMcpRequest(AbstractAIRequest, ABC):
	"""Abstract base class for MCP (Model Context Protocol) requests"""
	# Namespace ID for isolating MCP servers between different tenants
	namespaceId: Optional[str] = None
	# Unique identifier of the MCP server
	mcpId: Optional[str] = None
	# Name of the MCP server
	mcpName: Optional[str] = None

	def get_request_type(self) -> str:
		"""Returns the request type, must be implemented by subclasses"""
		raise NotImplementedError("Subclasses should implement this method.")


# Request type constants for MCP operations
QUERY_MCP_SERVER_REQUEST_TYPE = "QueryMcpServerRequest"
MCP_SERVER_ENDPOINT_REQUEST_TYPE = "McpServerEndpointRequest"
RELEASE_MCP_SERVER_REQUEST_TYPE = "ReleaseMcpServerRequest"


class QueryMcpServerRequest(AbstractMcpRequest):
	"""Request for querying MCP server details by name and version"""
	# Version of the MCP server to query
	version: Optional[str] = None

	def get_request_type(self) -> str:
		"""Returns the query MCP server request type"""
		return QUERY_MCP_SERVER_REQUEST_TYPE


class McpServerEndpointRequest(AbstractMcpRequest):
	"""Request for registering or deregistering MCP server endpoint"""
	# IP address or hostname of the MCP server
	address: Optional[str] = None
	# Port number of the MCP server
	port: Optional[int] = None
	# Version of the MCP server endpoint
	version: Optional[str] = None
	# Operation type: REGISTER_ENDPOINT or DE_REGISTER_ENDPOINT from AIConstants
	type: Optional[str] = None

	def get_request_type(self) -> str:
		"""Returns the MCP server endpoint request type"""
		return MCP_SERVER_ENDPOINT_REQUEST_TYPE


class ReleaseMcpServerRequest(AbstractMcpRequest):
	"""Request for releasing/publishing a new MCP server to the registry"""
	# Basic server information specification
	serverSpecification: Optional[McpServerBasicInfo] = None
	# Tool specification defining the capabilities of the MCP server
	toolSpecification: Optional[McpToolSpecification] = None
	# Endpoint specification for accessing the MCP server
	endpointSpecification: Optional[McpEndpointSpce] = None

	def get_request_type(self) -> str:
		"""Returns the release MCP server request type"""
		return RELEASE_MCP_SERVER_REQUEST_TYPE
