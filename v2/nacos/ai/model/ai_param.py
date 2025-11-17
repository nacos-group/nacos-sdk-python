from typing import Optional, Callable, Awaitable

from a2a.types import AgentCard
from pydantic import BaseModel

from v2.nacos.ai.model.a2a.a2a import AgentCardDetailInfo
from v2.nacos.ai.model.ai_constant import AIConstants
from v2.nacos.ai.model.mcp.mcp import McpServerBasicInfo, McpToolSpecification, \
	McpEndpointSpce, McpServerDetailInfo


class GetMcpServerParam(BaseModel):
	"""Parameter model for retrieving MCP server information"""
	# Name of the MCP server to query
	mcp_name: Optional[str] = None
	# Version of the MCP server to query
	version: Optional[str] = None


class ReleaseMcpServerParam(BaseModel):
	"""Parameter model for releasing/publishing MCP server"""
	# Basic information specification for the MCP server
	server_spec: Optional[McpServerBasicInfo] = None
	# Tool specification defining the tools provided by MCP server
	tool_spec: Optional[McpToolSpecification] = None
	# Endpoint specification for MCP server network configuration
	mcp_endpoint_spec: Optional[McpEndpointSpce] = None


class RegisterMcpServerEndpointParam(BaseModel):
	"""Parameter model for registering MCP server endpoint"""
	# Name of the MCP server
	mcp_name: Optional[str] = None
	# IP address or hostname of the MCP server endpoint
	address: Optional[str] = None
	# Port number of the MCP server endpoint
	port: Optional[int] = None
	# Version of the MCP server
	version: Optional[str] = None

class DeregisterMcpServerEndpointParam(BaseModel):
	"""Parameter model for deregistering MCP server endpoint"""
	# Name of the MCP server
	mcp_name: Optional[str] = None
	# IP address or hostname of the MCP server endpoint
	address: Optional[str] = None
	# Port number of the MCP server endpoint
	port: Optional[int] = None


class SubscribeMcpServerParam(BaseModel):
	"""Parameter model for subscribing to MCP server changes"""
	# Name of the MCP server to subscribe to
	mcp_name: Optional[str] = None
	# Version of the MCP server to subscribe to
	version: Optional[str] = None
	# Callback function to handle MCP server changes
	# Parameters: mcp_id, namespace_id, mcp_name, mcp_server_detail_info
	subscribe_callback: Optional[
		Callable[[str, str, str, McpServerDetailInfo], Awaitable[None]]] = None


class GetAgentCardParam(BaseModel):
	# name of agent card
	agent_name: str
	# target version, if null or empty, get latest version
	version: Optional[str] = None
	# AiConstants.A2a#A2A_ENDPOINT_TYPE_URL or AiConstants.A2a#A2A_ENDPOINT_TYPE_SERVICE default is empty, means use agent card setting in nacos.
	registration_type: Optional[str] = None


class ReleaseAgentCardParam(BaseModel):
	agent_card: AgentCard
	registration_type: Optional[str] = AIConstants.A2A_ENDPOINT_TYPE_SERVICE
	set_as_latest: Optional[bool] = False


class RegisterAgentEndpointParam(BaseModel):
	agent_name: str
	version: Optional[str] = None
	address: Optional[str] = None
	port: Optional[int] = None
	transport: Optional[str] = AIConstants.A2A_ENDPOINT_DEFAULT_TRANSPORT
	path: Optional[str] = None
	support_tls: Optional[bool] = False


class DeregisterAgentEndpointParam(BaseModel):
	agent_name: str
	version: Optional[str] = None
	address: Optional[str] = None
	port: Optional[int] = None


class SubscribeAgentCardParam(BaseModel):
	agent_name: str
	version: Optional[str] = None
	# Parameters: agent_name, agent_card_detail_info
	subscribe_callback: Optional[
		Callable[[str, AgentCardDetailInfo], Awaitable[None]]] = None