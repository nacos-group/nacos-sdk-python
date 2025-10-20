from __future__ import annotations

import hashlib
import json
import threading
from typing import Any, Callable, Dict, Optional, Type, TypeVar

import nacos
import yaml
from loguru import logger

from app import settings

T = TypeVar("T")

_client_lock = threading.RLock()
_client: Optional[nacos.NacosClient] = None

_state_lock = threading.RLock()
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

    with _state_lock:
        _state["raw"] = content
        _state["data"] = parsed
        _state["md5"] = md5
        snapshot = {
            "md5": md5,
            "data": parsed.copy(),
        }
        snapshot["raw"] = content
        return snapshot


def _snapshot(include_raw: bool = True) -> Dict[str, Any]:
    with _state_lock:
        raw = _state["raw"]
        data = _state["data"].copy()
        md5 = _state["md5"]
    snap: Dict[str, Any] = {"md5": md5, "data": data}
    if include_raw:
        snap["raw"] = raw
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


def _register_watcher(client: nacos.NacosClient) -> None:
    """Register config change watcher for different SDK versions."""
    if hasattr(client, "add_config_watcher"):
        client.add_config_watcher(settings.NACOS_DATA_ID, settings.NACOS_GROUP, _on_config_change)
    else:
        client.add_listener(settings.NACOS_DATA_ID, settings.NACOS_GROUP, _on_config_change)


def _unregister_watcher(client: nacos.NacosClient) -> None:
    try:
        if hasattr(client, "remove_config_watcher"):
            client.remove_config_watcher(settings.NACOS_DATA_ID, settings.NACOS_GROUP, _on_config_change)
        elif hasattr(client, "remove_listener"):
            client.remove_listener(settings.NACOS_DATA_ID, settings.NACOS_GROUP, _on_config_change)
    except Exception as exc:
        logger.warning(f"[Nacos] remove watcher failed: {exc}")


def init_nacos_config() -> nacos.NacosClient:
    """
    Initialize the Nacos client and snapshot using the SDK's own caching/failover.
    Returns the client for lifecycle management.
    """
    global _client

    with _client_lock:
        if _client is not None:
            return _client
        client = nacos.NacosClient(
            server_addresses=settings.NACOS_SERVER_ADDR,
            namespace=settings.NACOS_NAMESPACE,
            username=settings.NACOS_USERNAME or None,
            password=settings.NACOS_PASSWORD or None,
        )
        _client = client

    try:
        content = _client.get_config(settings.NACOS_DATA_ID, settings.NACOS_GROUP)
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

    _register_watcher(_client)
    logger.info("[Nacos] Config watcher/listener registered.")

    _notify(snapshot)
    return _client


def _on_config_change(args: Dict[str, Any]) -> None:
    """Callback invoked by the SDK when config changes."""
    data_id = args.get("dataId")
    group = args.get("group")
    content = args.get("content")

    snapshot = _update_state(content)
    logger.info(
        f"[Nacos][ConfigChanged] dataId={data_id}, group={group}, md5={snapshot['md5']}, keys={list(snapshot['data'].keys())}"
    )
    _notify(snapshot)


def stop_nacos_config(client: Optional[nacos.NacosClient]) -> None:
    """Remove watcher on shutdown."""
    if not client:
        return
    _unregister_watcher(client)


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
