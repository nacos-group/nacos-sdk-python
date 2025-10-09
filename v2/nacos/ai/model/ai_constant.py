class AIConstants:
	"""
	Constants used in AI module for MCP server registry operations
	"""

	# Operation type for registering MCP server endpoint
	REGISTER_ENDPOINT = "registerEndpoint"

	# Operation type for deregistering MCP server endpoint
	DE_REGISTER_ENDPOINT = "deregisterEndpoint"

	# Direct endpoint type: specify MCP server address and port directly
	MCP_ENDPOINT_TYPE_DIRECT = "DIRECT"

	# Reference endpoint type: reference to a service already registered in Nacos
	MCP_ENDPOINT_TYPE_REF = "REF"

	MCP_STATUS_ACTIVE = "active"

	MCP_STATUS_DEPRECATED = "deprecated"

	A2A_ENDPOINT_TYPE_URL = "URL"

	A2A_ENDPOINT_TYPE_SERVICE = "SERVICE"

	A2A_ENDPOINT_DEFAULT_TRANSPORT = "JSONRPC"