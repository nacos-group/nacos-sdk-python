from typing import Optional, Dict, Any

from pydantic import BaseModel


class SkillResource(BaseModel):
	"""Skill resource structure.

	A resource file belonging to a Skill, e.g. template, data, script, etc.
	"""

	# Resource name (includes file extension, e.g., config_check_template.json)
	name: Optional[str] = None
	# Resource type: template, data, script, etc.
	type: Optional[str] = None
	# Resource content (string format, read from independent configuration)
	content: Optional[str] = None
	# Resource metadata (optional)
	metadata: Optional[Dict[str, Any]] = None

	def get_resource_identifier(self) -> str:
		"""Get resource unique identifier.
		Format: "type::name" if type is not blank, otherwise "name".
		"""
		if self.type and self.type.strip():
			return f"{self.type}::{self.name}"
		return self.name or ""


class Skill(BaseModel):
	"""Skill entity for independent Skills management.

	Contains the SKILL.md content and associated resource files.
	"""

	# Namespace ID
	namespace_id: Optional[str] = None
	# Skill name (unique identifier)
	name: Optional[str] = None
	# Skill description
	description: Optional[str] = None
	# Full SKILL.md content
	skill_md: Optional[str] = None
	# Resource map (key is resource name)
	resource: Optional[Dict[str, SkillResource]] = None

	def __str__(self):
		return f"Skill(name='{self.name}', description='{self.description}')"
