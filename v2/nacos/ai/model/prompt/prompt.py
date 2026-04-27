from typing import Optional, Dict, List

from pydantic import BaseModel


class PromptVariable(BaseModel):
	"""Prompt variable definition with optional default value.

	Represents a variable placeholder (e.g., {{variableName}}) in a prompt template,
	along with its optional default value and description.
	"""

	name: Optional[str] = None
	defaultValue: Optional[str] = None
	description: Optional[str] = None

	def __str__(self):
		return f"PromptVariable(name='{self.name}', defaultValue='{self.defaultValue}', description='{self.description}')"


class Prompt(BaseModel):
	"""Prompt entity for AI Prompt management.

	Prompt is stored as a Nacos configuration with fixed group "nacos-ai-prompt"
	and dataId "{promptKey}.json". The content is stored as JSON format.
	"""

	promptKey: Optional[str] = None
	version: Optional[str] = None
	template: Optional[str] = None
	md5: Optional[str] = None
	variables: Optional[List[PromptVariable]] = None

	def render(self, variables: Optional[Dict[str, str]] = None) -> Optional[str]:
		"""Render the prompt template by replacing {{variableName}} with values.

		First applies default values from variable definitions (self.variables),
		then overrides with user-provided values.

		Example:
			prompt = Prompt(template="Hello {{name}}, welcome to {{place}}!")
			result = prompt.render({"name": "Alice", "place": "Nacos"})
			# Result: "Hello Alice, welcome to Nacos!"
		"""
		if self.template is None:
			return None

		merged = {}
		if self.variables is not None:
			for v in self.variables:
				if v.defaultValue is not None:
					merged[v.name] = v.defaultValue
		if variables is not None:
			merged.update(variables)

		if not merged:
			return self.template

		result = self.template
		for key, value in merged.items():
			placeholder = "{{" + key + "}}"
			result = result.replace(placeholder, value if value is not None else "")
		return result

	def __str__(self):
		return f"Prompt(promptKey='{self.promptKey}', version='{self.version}')"
