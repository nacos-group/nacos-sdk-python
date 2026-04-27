import base64
import io
import zipfile
from typing import Dict

from v2.nacos.ai.model.skill.skill import Skill, SkillResource

# ZIP local file header signature: PK\x03\x04
ZIP_MAGIC = b'\x50\x4B\x03\x04'

# Minimum valid ZIP size (local file header = 30 bytes)
ZIP_MIN_SIZE = 30

METADATA_ENCODING = "encoding"
METADATA_ENCODING_BASE64 = "base64"
PATH_TRAVERSAL_SEQUENCE = ".."


def validate_zip_bytes(data: bytes) -> None:
	"""Validate that byte array is a valid ZIP file by checking the magic number header."""
	if data is None or len(data) < ZIP_MIN_SIZE:
		size = 0 if data is None else len(data)
		raise ValueError(f"Invalid ZIP data: too short ({size} bytes)")
	if data[:4] != ZIP_MAGIC:
		raise ValueError("Invalid ZIP data: missing ZIP magic header (PK\\x03\\x04)")


def validate_path_safety(path: str) -> None:
	"""Validate that a path does not contain path traversal sequences or absolute path indicators."""
	if path is None:
		return
	if PATH_TRAVERSAL_SEQUENCE in path:
		raise SecurityError(f"Path traversal detected: {path}")
	if path.startswith("/") or path.startswith("\\"):
		raise SecurityError(f"Absolute path not allowed: {path}")


def validate_zip_entry_paths(data: bytes) -> None:
	"""Validate all ZIP entry paths for path traversal and absolute paths."""
	with zipfile.ZipFile(io.BytesIO(data), 'r') as zf:
		for entry in zf.namelist():
			validate_path_safety(entry)


def is_base64_encoded(resource: SkillResource) -> bool:
	"""Check if a resource is Base64-encoded binary content."""
	if resource.metadata is None:
		return False
	return resource.metadata.get(METADATA_ENCODING) == METADATA_ENCODING_BASE64


def resolve_resource_bytes(resource: SkillResource) -> bytes:
	"""Resolve resource content to raw bytes.
	Base64-encoded binary resources are decoded; text resources are returned as UTF-8 bytes.
	"""
	if resource.content is None:
		return b''
	if is_base64_encoded(resource):
		return base64.b64decode(resource.content)
	return resource.content.encode('utf-8')


def to_zip_bytes(skill: Skill) -> bytes:
	"""Convert Skill object to a ZIP byte array containing all skill files.

	The ZIP structure: skillName/SKILL.md, skillName/type/resourceName, etc.
	Binary resources (marked with metadata encoding=base64) are decoded back to raw bytes.
	"""
	if skill is None:
		raise ValueError("Skill cannot be None")
	if not skill.name or not skill.name.strip():
		raise ValueError("Skill name cannot be blank")

	skill_name = skill.name
	buf = io.BytesIO()
	with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
		# 1. SKILL.md
		skill_md_content = skill.skill_md if skill.skill_md else ""
		zf.writestr(f"{skill_name}/SKILL.md", skill_md_content)

		# 2. Resource files
		if skill.resource:
			for resource in skill.resource.values():
				if resource is None or not resource.name or not resource.name.strip():
					continue
				entry_path = _build_zip_entry_path(skill_name, resource)
				raw_bytes = resolve_resource_bytes(resource)
				zf.writestr(entry_path, raw_bytes)

	return buf.getvalue()


def _build_zip_entry_path(skill_name: str, resource: SkillResource) -> str:
	"""Build ZIP entry path for a skill resource."""
	if resource.type and resource.type.strip():
		entry_path = f"{skill_name}/{resource.type}/{resource.name}"
	else:
		entry_path = f"{skill_name}/{resource.name}"
	validate_path_safety(entry_path)
	return entry_path


class SecurityError(Exception):
	"""Raised when a security violation is detected (e.g. path traversal)."""
	pass
