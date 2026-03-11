from typing import Optional

LATEST_VERSION = "latest"


def build_prompt_cache_key(prompt_key: str, version: Optional[str], label: Optional[str]) -> str:
	"""Build a cache key for prompt using the same format as Java client's CacheKeyUtils."""
	if label and len(label) > 0:
		return f"{prompt_key}::label:{label}"
	if version and len(version) > 0:
		return f"{prompt_key}::version:{version}"
	return f"{prompt_key}::{LATEST_VERSION}"
