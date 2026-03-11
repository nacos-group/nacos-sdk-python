from typing import Optional, Dict

from pydantic import BaseModel


class Prompt(BaseModel):
	"""Prompt entity for AI Prompt management.

	Prompt is stored as a Nacos configuration with fixed group "nacos-ai-prompt"
	and dataId "{promptKey}.json". The content is stored as JSON format.
	"""

	promptKey: Optional[str] = None
	version: Optional[str] = None
	template: Optional[str] = None
	md5: Optional[str] = None

	def render(self, variables: Optional[Dict[str, str]] = None) -> Optional[str]:
		"""Render the prompt template by replacing {{variableName}} with values.

		Example:
			prompt = Prompt(template="Hello {{name}}, welcome to {{place}}!")
			result = prompt.render({"name": "Alice", "place": "Nacos"})
			# Result: "Hello Alice, welcome to Nacos!"
		"""
		if self.template is None:
			return None
		if not variables:
			return self.template

		result = self.template
		for key, value in variables.items():
			placeholder = "{{" + key + "}}"
			result = result.replace(placeholder, value if value is not None else "")
		return result

	def __str__(self):
		return f"Prompt(promptKey='{self.promptKey}', version='{self.version}')"
