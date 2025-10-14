from typing import Optional, List, Dict, Any

from a2a._base import A2ABaseModel
from a2a.types import AgentCard
from v2.nacos.ai.model.ai_constant import AIConstants


class AgentEndpoint(A2ABaseModel):
	transport: Optional[str] = AIConstants.A2A_ENDPOINT_DEFAULT_TRANSPORT
	address: Optional[str] = None
	port: Optional[int] = None
	path: Optional[str] = ""
	support_tls: Optional[bool] = False
	version: Optional[str] = None

	def __eq__(self, other):
		# 检查是否为同一类型
		if not isinstance(other, AgentEndpoint):
			return False

		# 检查所有属性是否相等
		return (self.transport == other.transport and
				self.address == other.address and
				self.port == other.port and
				self.path == other.path and
				self.support_tls == other.support_tls and
				self.version == other.version)

	def __hash__(self):
		# 如果需要支持将 AgentEndpoint 作为字典键或放入集合中，可以实现 __hash__
		return hash((self.transport, self.address, self.port,
					 self.path, self.support_tls, self.version))


class AgentCardDetailInfo(AgentCard):
	registration_type: Optional[str] = AIConstants.A2A_ENDPOINT_TYPE_URL
	latest_version: Optional[bool] = False

# class AgentExtension(BaseModel):
# 	uri : Optional[str] = None
# 	description : Optional[str] = None
# 	required : Optional[bool] = False
# 	params : Optional[Dict[str, Any]] = []
#
# class AgentCapabilities(BaseModel):
# 	streaming : Optional[bool] = False
# 	pushNotification : Optional[bool] = False
# 	stateTransitionHistory : Optional[bool] = False
# 	extensions : Optional[List[AgentExtension]] = []
#
# class AgentSkill(BaseModel):
# 	id : Optional[str] = None
# 	name : Optional[str] = None
# 	description : Optional[str] = None
# 	tags : Optional[List[str]] = []
# 	examples : Optional[List[str]] = []
#
# class AgentInterface(BaseModel):
# 	pass
#
# class AgentProvider(BaseModel):
# 	pass
#
# class AgentCardBasicInfo(BaseModel):
# 	protocolVersion: Optional[str] = None
# 	name: Optional[str] = None
# 	description: Optional[str] = None
# 	version: Optional[str] = None
# 	iconUrl: Optional[str] = None
# 	capabilities: Optional[AgentCapabilities] = None
# 	skills: Optional[List[AgentSkill]] = []
#
#
# class AgentCard(BaseModel):
# 	url: Optional[str] = None
# 	preferredTransport: Optional[str] = None
# 	additionalInterfaces: Optional[List[AgentInterface]] = []
# 	provider: Optional[AgentProvider] = None
# 	documentationUrl: Optional[str] = None
# 	securitySchemas: Optional[Dict[str, Any]] = []
# 	security: Optional[Dict[str,List[str]]] = []
# 	defaultInputModes: Optional[List[str]] = []
# 	defaultOutputModes: Optional[List[str]] = []
# 	supportsAuthenticatedExtendedCard: Optional[bool] = False
