from typing import Optional

LATEST_VERSION = "latest"

def build_mcp_server_key(mcp_name: str, version: Optional[str]) -> str:
	if version is None or len(version) == 0:
		version = LATEST_VERSION

	return f"{mcp_name}::{version}"