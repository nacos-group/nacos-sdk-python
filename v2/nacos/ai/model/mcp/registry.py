from abc import ABC
from typing import Optional, List, Dict, Literal, Any

from pydantic import Field, BaseModel


class Input(BaseModel):
	"""Input parameter definition for MCP tools and configurations"""
	# Description of the input parameter
	description: Optional[str] = None
	# Whether this input parameter is required
	isRequired: Optional[bool] = Field(None, alias='is_required')
	# Format specification for the input value
	format: Optional[str] = None
	# Current value of the input parameter
	value: Optional[str] = None
	# Whether this input contains sensitive/secret information
	isSecret: Optional[bool] = Field(None, alias='is_secret')
	# Default value for the input parameter
	defaultValue: Optional[str] = Field(None, alias='default_value')
	# List of valid choices for the input parameter
	choices: Optional[List[str]] = None


class InputWithVariables(Input):
	"""Input parameter with nested variable definitions"""
	# Dictionary of nested input variables
	variables: Optional[Dict[str, Input]] = None


class KeyValueInput(InputWithVariables):
	"""Key-value pair input parameter with variable support"""
	# Name of the key-value input parameter
	name: Optional[str] = None


class Argument(BaseModel,ABC):
	"""Abstract base class for MCP tool arguments"""
	pass


class PositionalArgument(Argument):
	"""Positional argument for MCP tool execution"""
	# Argument type identifier
	type: Literal["positional"] = "positional"
	# Hint about the expected value format
	valueHint: Optional[str] = None
	# Whether this argument can be repeated multiple times
	isRepeated: Optional[bool] = Field(None, alias='is_repeated')

class NamedArgument(Argument):
	"""Named argument for MCP tool execution"""
	# Argument type identifier
	type: Literal["named"] = "named"
	# Name of the named argument
	name: Optional[str] = None
	# Whether this argument can be repeated multiple times
	isRepeated: Optional[bool] = Field(None, alias='is_repeated')


class Package(BaseModel):
	"""Package definition for MCP server deployment"""
	# Name of the package registry
	registryType: Optional[str] = Field(None, alias='registry_type')
	# Name of the package
	registryBaseUrl: Optional[ str ] = Field(None, alias='registry_base_url')

	identifier: Optional[str]
	# Version of the package
	version: Optional[str] = None

	fileSha256: Optional[str] = Field(None, alias='file_sha256')
	# Hint about the runtime environment required
	runtimeHint: Optional[str] = Field(None, alias='runtime_hint')
	# Arguments for the runtime environment
	runtimeArguments: Optional[List[Argument]] = Field(None,
													   alias='runtime_arguments')
	# Arguments for the package itself
	packageArguments: Optional[List[Argument]] = Field(None,
													   alias='package_arguments')
	# Environment variables required by the package
	environmentVariables: Optional[List[KeyValueInput]] = Field(None,
																alias='environment_variables')


class Repository(BaseModel):
	"""Repository information for MCP server source code"""
	# URL of the repository
	url: Optional[str] = None
	# Source location or path within the repository
	source: Optional[str] = None
	# Unique identifier of the repository
	id: Optional[str] = None

	subfolder: Optional[str] = Field(None, alias='subfolder')


class ServerVersionDetail(BaseModel):
	"""Version details for MCP server"""
	# Version string of the MCP server
	version: Optional[str] = None
	# Release date information
	release_data: Optional[str] = None
	# Whether this is the latest version
	is_latest: Optional[bool] = False
