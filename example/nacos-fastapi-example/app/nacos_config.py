from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any, Callable, Dict, Optional, Type, TypeVar

import yaml
from loguru import logger

from v2.nacos import NacosConfigService, ClientConfigBuilder, ConfigParam, GRPCConfig
from app import settings

T = TypeVar("T")

_client_lock = asyncio.Lock()
_client: Optional[NacosConfigService] = None

_state: Dict[str, Any] = {
    "raw": "",
    "data": {},
    "md5": None,
}

_subscribers: list[Callable[[Dict[str, Any]], None]] = []


def _parse_text(text: Optional[str]) -> Dict[str, Any]:
    """Parse config content as YAML first, then JSON."""
    if not text:
        return {}
    try:
        parsed = yaml.safe_load(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return {}


def _update_state(raw: Optional[str]) -> Dict[str, Any]:
    """Update in-memory snapshot and return a shallow copy for observers."""
    content = raw or ""
    parsed = _parse_text(content)
    md5 = hashlib.md5(content.encode("utf-8")).hexdigest() if content else None

    _state["raw"] = content
    _state["data"] = parsed
    _state["md5"] = md5
    return {
        "md5": md5,
        "data": parsed.copy(),
        "raw": content,
    }


def _snapshot(include_raw: bool = True) -> Dict[str, Any]:
    snap: Dict[str, Any] = {"md5": _state["md5"], "data": _state["data"].copy()}
    if include_raw:
        snap["raw"] = _state["raw"]
    return snap


def subscribe(callback: Callable[[Dict[str, Any]], None]) -> None:
    """Subscribe to config changes. Callback receives the current snapshot."""
    _subscribers.append(callback)


def unsubscribe(callback: Callable[[Dict[str, Any]], None]) -> None:
    try:
        _subscribers.remove(callback)
    except ValueError:
        pass


def _notify(snapshot: Dict[str, Any]) -> None:
    for cb in list(_subscribers):
        try:
            cb(snapshot)
        except Exception as exc:
            logger.warning(f"[ConfigSubscriber] callback error: {exc}")


async def init_nacos_config() -> NacosConfigService:
    """
    Initialize the Nacos V2 config client (async + gRPC).
    Returns the client for lifecycle management.
    """
    global _client

    async with _client_lock:
        if _client is not None:
            return _client

        client_config = (ClientConfigBuilder()
                         .server_address(settings.NACOS_SERVER_ADDR)
                         .namespace_id(settings.NACOS_NAMESPACE)
                         .username(settings.NACOS_USERNAME)
                         .password(settings.NACOS_PASSWORD)
                         .log_level('INFO')
                         .grpc_config(GRPCConfig(grpc_timeout=5000))
                         .build())

        client = await NacosConfigService.create_config_service(client_config)
        _client = client

    try:
        content = await _client.get_config(ConfigParam(
            data_id=settings.NACOS_DATA_ID,
            group=settings.NACOS_GROUP,
        ))
    except Exception as exc:
        logger.error(f"[Nacos] Failed to load config via SDK: {exc}")
        content = None

    snapshot = _update_state(content)
    if content:
        logger.info(
            f"[Nacos][ConfigLoaded] dataId={settings.NACOS_DATA_ID}, group={settings.NACOS_GROUP}, md5={snapshot['md5']}"
        )
    else:
        logger.warning(
            "[Nacos] Config content is empty; relying on SDK failover/local snapshot if available."
        )

    await _client.add_listener(settings.NACOS_DATA_ID, settings.NACOS_GROUP, _on_config_change)
    logger.info("[Nacos] Config listener registered.")

    _notify(snapshot)
    return _client


async def _on_config_change(tenant: str, group: str, data_id: str, content: str) -> None:
    """Callback invoked by the V2 SDK when config changes (via gRPC push)."""
    snapshot = _update_state(content)
    logger.info(
        f"[Nacos][ConfigChanged] dataId={data_id}, group={group}, md5={snapshot['md5']}, keys={list(snapshot['data'].keys())}"
    )
    _notify(snapshot)


async def stop_nacos_config(client: Optional[NacosConfigService]) -> None:
    """Shutdown the V2 config client and release gRPC resources."""
    global _client
    if not client:
        return
    await client.shutdown()
    _client = None


def get_config_snapshot(include_raw: bool = True) -> Dict[str, Any]:
    """Return current parsed config snapshot."""
    return _snapshot(include_raw=include_raw)


def _dig(d: dict, path: str) -> Any:
    current: Any = d
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def get_value(path: str, default: T | None = None, cast: Callable[[Any], T] | None = None) -> T | Any | None:
    data = get_config_snapshot(include_raw=False)["data"]
    val = _dig(data, path)
    if val is None:
        return default
    if cast:
        try:
            return cast(val)
        except Exception:
            return default
    return val


def get_section(path: str) -> dict:
    data = get_config_snapshot(include_raw=False)["data"]
    val = _dig(data, path)
    return val if isinstance(val, dict) else {}


def load_typed(model: Type[T], section: Optional[str] = None, use_cache: bool = True) -> T:
    """
    Validate config using a pydantic model. `use_cache` parameter is kept for compatibility
    but the SDK-driven approach always refreshes from the latest snapshot.
    """
    from pydantic import BaseModel

    if not issubclass(model, BaseModel):
        raise TypeError("model must be a pydantic BaseModel subclass")

    data = get_section(section) if section else get_config_snapshot(include_raw=False)["data"]
    return model.model_validate(data)  # type: ignore[return-value]
