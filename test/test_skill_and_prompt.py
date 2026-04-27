import base64
import io
import json
import unittest
import zipfile

from v2.nacos.ai.model.prompt.prompt import Prompt, PromptVariable
from v2.nacos.ai.model.skill.skill import Skill, SkillResource
from v2.nacos.ai.util.skill_util import (
	SecurityError,
	to_zip_bytes,
	validate_zip_bytes,
	validate_zip_entry_paths,
	resolve_resource_bytes,
)


class TestPromptVariable(unittest.TestCase):
	"""Tests for PromptVariable model."""

	def test_create_prompt_variable(self):
		v = PromptVariable(name="city", defaultValue="Hangzhou", description="Target city")
		self.assertEqual(v.name, "city")
		self.assertEqual(v.defaultValue, "Hangzhou")
		self.assertEqual(v.description, "Target city")

	def test_create_prompt_variable_defaults(self):
		v = PromptVariable()
		self.assertIsNone(v.name)
		self.assertIsNone(v.defaultValue)
		self.assertIsNone(v.description)


class TestPromptRender(unittest.TestCase):
	"""Tests for Prompt.render() with variable default values."""

	def _make_prompt(self, template, variables=None):
		return Prompt(
			promptKey="test-key",
			version="1.0",
			template=template,
			variables=variables,
		)

	def test_render_uses_defaults_when_no_user_params(self):
		prompt = self._make_prompt(
			"Hello {{name}}, welcome to {{place}}!",
			variables=[
				PromptVariable(name="name", defaultValue="World"),
				PromptVariable(name="place", defaultValue="Nacos"),
			],
		)
		result = prompt.render()
		self.assertEqual(result, "Hello World, welcome to Nacos!")

	def test_render_user_params_partial_override(self):
		prompt = self._make_prompt(
			"Hello {{name}}, welcome to {{place}}!",
			variables=[
				PromptVariable(name="name", defaultValue="World"),
				PromptVariable(name="place", defaultValue="Nacos"),
			],
		)
		result = prompt.render({"name": "Alice"})
		self.assertEqual(result, "Hello Alice, welcome to Nacos!")

	def test_render_user_params_full_override(self):
		prompt = self._make_prompt(
			"Hello {{name}}, welcome to {{place}}!",
			variables=[
				PromptVariable(name="name", defaultValue="World"),
				PromptVariable(name="place", defaultValue="Nacos"),
			],
		)
		result = prompt.render({"name": "Bob", "place": "Shanghai"})
		self.assertEqual(result, "Hello Bob, welcome to Shanghai!")

	def test_render_backward_compat_variables_none(self):
		"""When self.variables is None, render should still work with user params."""
		prompt = self._make_prompt("Hello {{name}}!", variables=None)
		result = prompt.render({"name": "Alice"})
		self.assertEqual(result, "Hello Alice!")

	def test_render_backward_compat_no_variables_no_params(self):
		"""When both variables and params are absent, template returned as-is."""
		prompt = self._make_prompt("Hello {{name}}!", variables=None)
		result = prompt.render()
		self.assertEqual(result, "Hello {{name}}!")

	def test_render_template_none(self):
		prompt = self._make_prompt(None)
		self.assertIsNone(prompt.render({"name": "Alice"}))

	def test_render_default_with_none_value(self):
		"""Default value that is None should not be merged; placeholder stays."""
		prompt = self._make_prompt(
			"Hello {{name}}!",
			variables=[PromptVariable(name="name", defaultValue=None)],
		)
		result = prompt.render()
		self.assertEqual(result, "Hello {{name}}!")

	def test_deserialize_prompt_with_variables(self):
		"""Deserialize a Prompt from JSON that includes variables."""
		data = {
			"promptKey": "greeting",
			"version": "2.0",
			"template": "Hi {{user}}",
			"variables": [
				{"name": "user", "defaultValue": "guest", "description": "Username"},
			],
		}
		prompt = Prompt(**data)
		self.assertEqual(prompt.promptKey, "greeting")
		self.assertEqual(len(prompt.variables), 1)
		self.assertEqual(prompt.variables[0].name, "user")
		self.assertEqual(prompt.variables[0].defaultValue, "guest")
		# Ensure render works on deserialized prompt
		self.assertEqual(prompt.render(), "Hi guest")


class TestSkillModel(unittest.TestCase):
	"""Tests for Skill / SkillResource model creation."""

	def test_create_skill_resource(self):
		r = SkillResource(name="tpl.json", type="template", content='{"key":"val"}')
		self.assertEqual(r.name, "tpl.json")
		self.assertEqual(r.type, "template")
		self.assertEqual(r.get_resource_identifier(), "template::tpl.json")

	def test_resource_identifier_no_type(self):
		r = SkillResource(name="readme.txt")
		self.assertEqual(r.get_resource_identifier(), "readme.txt")

	def test_create_skill(self):
		skill = Skill(
			namespace_id="public",
			name="my-skill",
			description="A test skill",
			skill_md="# My Skill",
			resource={
				"tpl": SkillResource(name="tpl.json", type="template", content="{}"),
			},
		)
		self.assertEqual(skill.name, "my-skill")
		self.assertEqual(skill.description, "A test skill")
		self.assertIn("tpl", skill.resource)


class TestSkillUtilToZipBytes(unittest.TestCase):
	"""Tests for skill_util.to_zip_bytes."""

	def _make_skill(self, name="test-skill", skill_md="# Test", resources=None):
		return Skill(name=name, skill_md=skill_md, resource=resources)

	def test_to_zip_basic(self):
		skill = self._make_skill()
		data = to_zip_bytes(skill)
		# Verify it's a valid ZIP
		with zipfile.ZipFile(io.BytesIO(data), 'r') as zf:
			names = zf.namelist()
			self.assertIn("test-skill/SKILL.md", names)
			self.assertEqual(zf.read("test-skill/SKILL.md").decode(), "# Test")

	def test_to_zip_with_typed_resource(self):
		resources = {
			"cfg": SkillResource(name="config.json", type="template", content='{"a":1}'),
		}
		skill = self._make_skill(resources=resources)
		data = to_zip_bytes(skill)
		with zipfile.ZipFile(io.BytesIO(data), 'r') as zf:
			self.assertIn("test-skill/template/config.json", zf.namelist())
			self.assertEqual(zf.read("test-skill/template/config.json").decode(), '{"a":1}')

	def test_to_zip_with_untyped_resource(self):
		resources = {
			"readme": SkillResource(name="README.txt", content="hello"),
		}
		skill = self._make_skill(resources=resources)
		data = to_zip_bytes(skill)
		with zipfile.ZipFile(io.BytesIO(data), 'r') as zf:
			self.assertIn("test-skill/README.txt", zf.namelist())

	def test_to_zip_with_base64_resource(self):
		raw = b'\x89PNG_FAKE_BINARY'
		encoded = base64.b64encode(raw).decode()
		resources = {
			"img": SkillResource(
				name="icon.png",
				type="data",
				content=encoded,
				metadata={"encoding": "base64"},
			),
		}
		skill = self._make_skill(resources=resources)
		data = to_zip_bytes(skill)
		with zipfile.ZipFile(io.BytesIO(data), 'r') as zf:
			self.assertEqual(zf.read("test-skill/data/icon.png"), raw)

	def test_to_zip_none_skill_raises(self):
		with self.assertRaises(ValueError):
			to_zip_bytes(None)

	def test_to_zip_blank_name_raises(self):
		with self.assertRaises(ValueError):
			to_zip_bytes(Skill(name="  ", skill_md="x"))

	def test_to_zip_empty_name_raises(self):
		with self.assertRaises(ValueError):
			to_zip_bytes(Skill(name="", skill_md="x"))

	def test_to_zip_no_skill_md(self):
		"""skill_md is None → SKILL.md should contain empty string."""
		skill = self._make_skill(skill_md=None)
		data = to_zip_bytes(skill)
		with zipfile.ZipFile(io.BytesIO(data), 'r') as zf:
			self.assertEqual(zf.read("test-skill/SKILL.md").decode(), "")


class TestValidateZipBytes(unittest.TestCase):
	"""Tests for validate_zip_bytes on invalid data."""

	def test_none_raises(self):
		with self.assertRaises(ValueError) as ctx:
			validate_zip_bytes(None)
		self.assertIn("too short", str(ctx.exception))

	def test_short_data_raises(self):
		with self.assertRaises(ValueError):
			validate_zip_bytes(b'\x00' * 10)

	def test_wrong_magic_raises(self):
		with self.assertRaises(ValueError) as ctx:
			validate_zip_bytes(b'\x00' * 50)
		self.assertIn("magic header", str(ctx.exception))

	def test_valid_zip_passes(self):
		buf = io.BytesIO()
		with zipfile.ZipFile(buf, 'w') as zf:
			zf.writestr("test.txt", "hello")
		validate_zip_bytes(buf.getvalue())  # should not raise


class TestResolveResourceBytes(unittest.TestCase):
	"""Tests for resolve_resource_bytes."""

	def test_text_resource(self):
		r = SkillResource(name="a.txt", content="hello")
		self.assertEqual(resolve_resource_bytes(r), b"hello")

	def test_base64_resource(self):
		raw = b'\x01\x02\x03'
		encoded = base64.b64encode(raw).decode()
		r = SkillResource(name="bin", content=encoded, metadata={"encoding": "base64"})
		self.assertEqual(resolve_resource_bytes(r), raw)

	def test_none_content(self):
		r = SkillResource(name="empty")
		self.assertEqual(resolve_resource_bytes(r), b'')


class TestValidateZipEntryPaths(unittest.TestCase):
	"""Tests for validate_zip_entry_paths path traversal detection."""

	def _make_zip_with_entry(self, entry_name):
		buf = io.BytesIO()
		with zipfile.ZipFile(buf, 'w') as zf:
			zf.writestr(entry_name, "data")
		return buf.getvalue()

	def test_safe_path_passes(self):
		data = self._make_zip_with_entry("skill/SKILL.md")
		validate_zip_entry_paths(data)  # should not raise

	def test_path_traversal_raises(self):
		data = self._make_zip_with_entry("skill/../../etc/passwd")
		with self.assertRaises(SecurityError):
			validate_zip_entry_paths(data)

	def test_absolute_path_raises(self):
		data = self._make_zip_with_entry("/etc/passwd")
		with self.assertRaises(SecurityError):
			validate_zip_entry_paths(data)

	def test_backslash_absolute_path_raises(self):
		data = self._make_zip_with_entry("\\Windows\\System32\\evil.dll")
		with self.assertRaises(SecurityError):
			validate_zip_entry_paths(data)


if __name__ == "__main__":
	unittest.main()
