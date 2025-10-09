from typing import Optional, List, Dict, Any

from pydantic import BaseModel

from v2.nacos.ai.model.ai_constant import AIConstants
from v2.nacos.ai.model.mcp.mcp import SecuritySchema


class AgentEndpoint(BaseModel):
	transport: Optional[str] = AIConstants.A2A_ENDPOINT_DEFAULT_TRANSPORT
	address: Optional[str] = None
	port: Optional[int] = None
	path: Optional[str] = ""
	supportTls: Optional[bool] = False
	version: Optional[str] = None

class AgentCapabilities(BaseModel):
	pass

class AgentSkill(BaseModel):
	pass

class AgentInterface(BaseModel):
	pass

class AgentProvider(BaseModel):
	pass

class AgentCardBasicInfo(BaseModel):
	protocolVersion: Optional[str] = None
	name: Optional[str] = None
	description: Optional[str] = None
	version: Optional[str] = None
	iconUrl: Optional[str] = None
	capabilities: Optional[AgentCapabilities] = None
	skills: Optional[List[AgentSkill]] = []


class AgentCard(BaseModel):
	url: Optional[str] = None
	preferredTransport: Optional[str] = None
	additionalInterfaces: Optional[List[AgentInterface]] = []
	provider: Optional[AgentProvider] = None
	documentationUrl: Optional[str] = None
	securitySchemas: Optional[Dict[str, Any]] = []
	security: Optional[Dict[str,List[str]]] = []
	defaultInputModes: Optional[List[str]] = []
	defaultOutputModes: Optional[List[str]] = []
	supportsAuthenticatedExtendedCard: Optional[bool] = False