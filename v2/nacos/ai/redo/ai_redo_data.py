from typing import Any, Optional

from pydantic import BaseModel

from v2.nacos.ai.model.a2a.a2a import AgentEndpoint
from v2.nacos.redo.redo_data import RedoData


class McpServerEndpointRedoData(RedoData):

	def __init__(self, data: Any, mcp_name: str) -> None:
		super().__init__(data)
		self.mcp_name = mcp_name


class McpServerEndpoint(BaseModel):
	address: Optional[str] = None
	port: Optional[int] = None
	version: Optional[str] = None

	def __eq__(self, other):
		if isinstance(other, McpServerEndpoint):
			return self.address == other.address and self.port == other.port and self.version == other.version
		return False


class AgentEndpointRedoData(RedoData):

	def __init__(self, data: AgentEndpoint, agent_name: str) -> None:
		super().__init__(data)
		self.agent_name = agent_name
