from enum import Enum, auto
from typing import Dict


class AbilityMode(Enum):
	SERVER = auto()
	SDK_CLIENT = auto()


class AbilityKey(Enum):
	SERVER_PERSISTENT_INSTANCE_BY_GRPC = (
		"supportPersistentInstanceByGrpc",
		"support persistent instance by grpc",
		AbilityMode.SERVER)

	SERVER_FUZZY_WATCH = (
		"fuzzyWatch", "Server whether support fuzzy watch service or config",
		AbilityMode.SERVER)

	SERVER_DISTRIBUTED_LOCK = (
		"lock", "Server whether support distributed lock",
		AbilityMode.SERVER)

	SERVER_MCP_REGISTRY = ("mcp",
						   "Server whether support release mcp server and register endpoint for mcp server",
						   AbilityMode.SERVER)

	SDK_CLIENT_FUZZY_WATCH = ("fuzzyWatch",
							  "Client whether support fuzzy watch service or config",
							  AbilityMode.SDK_CLIENT)

	SDK_CLIENT_DISTRIBUTED_LOCK = ("lock",
								   "Client whether support distributed lock",
								   AbilityMode.SDK_CLIENT)

	SDK_MCP_REGISTRY = ("mcp",
						"Client whether support release mcp server and register endpoint for mcp server",
						AbilityMode.SDK_CLIENT)

	SERVER_AGENT_REGISTRY = ("agent",
							"Server whether support release agent server and register endpoint for agent server",
							AbilityMode.SERVER)

	SDK_AGENT_REGISTRY = ("agent",
						"Client whether support release agent server and register endpoint for agent server",
						AbilityMode.SDK_CLIENT)

	def __init__(self, key_name: str, description: str, mode: AbilityMode):
		self.key_name = key_name
		self.description = description
		self.mode = mode


class AbilityStatus(Enum):
	SUPPORTED = auto()
	NOT_SUPPORTED = auto()
	UNKNOWN = auto()


SDK_ABILITY_TABLE: Dict[str, bool] = {
	AbilityKey.SDK_MCP_REGISTRY.key_name: True,
	AbilityKey.SDK_AGENT_REGISTRY.key_name: True,
}
