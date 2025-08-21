from typing import Optional, Callable, Awaitable

from pydantic import BaseModel

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
