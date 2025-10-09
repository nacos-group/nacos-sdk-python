from abc import ABC
from enum import Enum
from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel, Field

from v2.nacos.ai.model.ai_constant import AIConstants
from v2.nacos.ai.model.mcp.registry import Repository, Package, \
	ServerVersionDetail, KeyValueInput


class McpServiceRef(BaseModel):
	"""Reference to an MCP service registered in Nacos"""
	# Namespace ID where the service is registered
	namespaceId: Optional[str] = None
	# Group name of the service
	groupName: Optional[str] = None
	# Name of the service
	serviceName: Optional[str] = None
	# Transport protocol used by the service，current only support http/https
	transportProtocol: Optional[str] = None


class FrontEndpointConfig(BaseModel):
	"""Frontend endpoint configuration for MCP server access, address of higress or spring ai alibaba mcp gateway"""
	# Type of the frontend endpoint mcp-sse/mcp-streamable
	type: Optional[str] = None
	# Protocol used by the frontend endpoint (http, https, etc.)
	protocol: Optional[str] = None
	# Type classification of the endpoint direct/ref
	endpointType: Optional[str] = None
	# Data specific to the endpoint type
	endpointData: Optional[Any] = None
	# URL path for the endpoint
	path: Optional[str] = None
	# HTTP headers required for the endpoint
	headers: Optional[List[KeyValueInput]] = None


class McpServerRemoteServiceConfig(BaseModel):
	"""Configuration for MCP server remote service access"""
	# Reference to the remote service in Nacos
	serviceRef: Optional[McpServiceRef] = None
	# Export path for the remote service
	exportPath: Optional[str] = None
	# List of frontend endpoint configurations
	frontEndpointConfigList: Optional[List[FrontEndpointConfig]] = []


class McpCapability(Enum):
	"""Enumeration of MCP server capabilities"""
	# Tool capability: server provides executable tools
	TOOL = "TOOL"
	# Prompt capability: server provides prompts
	PROMPT = "PROMPT"
	# Resource capability: server provides resources
	RESOURCE = "RESOURCE"


class McpServerBasicInfo(BaseModel):
	"""Basic information about an MCP server"""
	# Unique identifier of the MCP server
	id: Optional[str] = None
	# Name of the MCP server
	name: Optional[str] = None
	# Backend protocol used by the MCP server.
	# When value is 'mcp-sse' or 'mcp-streamable' or 'stdio', it indicates native MCP server protocol support.
	# When value is 'http' or 'https', it indicates legacy interface conversion.
	protocol: Optional[str] = None
	# Frontend protocol for client access mcp-sse/mcp-streamable
	frontProtocol: Optional[str] = None
	# Description of the MCP server
	description: Optional[str] = None
	# Repository information for the server source code
	repository: Optional[Repository] = None
	# List of packages required for the server
	packages: Optional[List[Package]] = None
	# Detailed version information
	versionDetail: Optional[ServerVersionDetail] = None
	# Version string of the server, deprecated, please use versionDetail.version instead
	version: Optional[str] = None
	# Configuration for remote service access
	remoteServerConfig: Optional[McpServerRemoteServiceConfig] = None
	# Configuration for local server deployment
	localServerConfig: Optional[Dict[str, Any]] = None
	# Whether the server is enabled
	enabled: Optional[bool] = True
	# Current lifecycle status of MCP server, should be one of 'active' or 'deprecated'
	status: Optional[str] = AIConstants.MCP_STATUS_ACTIVE
	# List of capabilities provided by the server
	capabilities: Optional[List[McpCapability]] = None


class McpEndpointInfo(BaseModel):
	"""Endpoint information for accessing MCP server"""
	# Protocol used by the endpoint http/https
	protocol: Optional[str] = None
	# IP address or hostname of the MCP server
	address: Optional[str] = None
	# Port number of the MCP server
	port: Optional[int] = None
	# URL path for the endpoint
	path: Optional[str] = None
	# HTTP headers required for endpoint access
	headers: Optional[List[KeyValueInput]] = None


class McpTool(BaseModel):
	"""Definition of a tool provided by MCP server"""
	# Name of the tool
	name: Optional[str] = None
	# Description of what the tool does
	description: Optional[str] = None
	# JSON schema defining the input parameters for the tool
	inputSchema: Optional[Dict[str, Any]] = None


class McpToolMeta(BaseModel):
	"""Metadata for MCP tool configuration"""
	# Context information for tool invocation
	invokeContext: Optional[Dict[str, str]] = None
	# Whether the tool is enabled
	enabled: Optional[bool] = True
	# Templates for tool usage
	templates: Optional[Dict[str, Any]] = None


class SecuritySchema(BaseModel):
	"""Security schema definition for MCP tool access"""
	# Unique identifier of the security schema
	id: Optional[str] = None
	# Type of security (API key, OAuth, etc.)
	type: Optional[str] = None
	# Schema definition for the security mechanism
	schema_field: Optional[str] = Field(None, alias="schema")
	# Location where the security credential should be included
	in_: Optional[str] = Field(None, alias="in")
	# Name of the security parameter
	name: Optional[str] = None
	# Default credential value if available
	defaultCredential: Optional[str] = None

class EncryptObject (BaseModel):
	data: Optional[str] = None
	encryptInfo: Optional[Dict[str,str]] = None


class McpToolSpecification(BaseModel):
	"""Complete specification of tools provided by MCP server"""
	specificationType: Optional[str] = None
	encryptData: Optional[EncryptObject] = None
	# List of tools available on the MCP server
	tools: Optional[List[McpTool]] = None
	# Metadata for each tool, keyed by tool name
	toolsMeta: Optional[Dict[str, McpToolMeta]] = None
	# Security schemas required for tool access
	securitySchema: Optional[List[SecuritySchema]] = None


class McpServerDetailInfo(McpServerBasicInfo):
	"""Detailed information about an MCP server including endpoints and tools"""
	# List of backend endpoints for internal server communication
	backendEndpoints: Optional[List[McpEndpointInfo]] = None
	# List of frontend endpoints for client access
	frontendEndpoints: Optional[List[McpEndpointInfo]] = None
	# Complete tool specification provided by the server
	toolSpec: Optional[McpToolSpecification] = None
	# List of all available versions of the server
	allVersions: Optional[List[ServerVersionDetail]] = None
	# Namespace ID where the server is registered
	namespaceId: Optional[str] = None


class McpEndpointSpce(BaseModel):
	"""Specification for MCP server endpoint configuration"""
	# Endpoint type: Should be AIConstants.MCP_ENDPOINT_TYPE_DIRECT or AIConstants.MCP_ENDPOINT_TYPE_REF
	# DIRECT: specify address and port directly
	# REF: reference to a service already registered in Nacos
	type: Optional[str] = None

	# Endpoint data, format depends on type:
	# For DIRECT type: should include 'address' and 'port' keys
	# For REF type: should include 'groupName' and 'serviceName' keys
	data: Optional[Dict[str, str]] = None


