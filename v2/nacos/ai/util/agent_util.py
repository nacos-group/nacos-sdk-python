from typing import Optional

from v2.nacos import Instance
from v2.nacos.ai.model.a2a.a2a import AgentEndpoint
from v2.nacos.common.nacos_exception import INVALID_PARAM, NacosException

LATEST_VERSION = "latest"

def validate_agent_card_field(field_name: str, field_value: str):
	if field_value is None or len(field_value) == 0:
		raise NacosException(INVALID_PARAM, f"Required parameter `agentCard.{field_name}` is empty")

def validate_agent_endpoint(agent_endpoint: AgentEndpoint):
	if not agent_endpoint:
		raise NacosException(INVALID_PARAM, "Required parameter `agentEndpoint` can not be null")
	if not agent_endpoint.version or len(agent_endpoint.version) == 0:
		raise NacosException(INVALID_PARAM, "Required parameter `agentEndpoint.version` can not be empty")

	instance = Instance(
			ip=agent_endpoint.address,
			port=agent_endpoint.port,
	)

	instance.check_instance_is_legal()

def build_agent_key(mcp_name: str, version: Optional[str]) -> str:
	if version is None or len(version) == 0:
		version = LATEST_VERSION

	return f"{mcp_name}::{version}"