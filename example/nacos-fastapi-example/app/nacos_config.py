# app/nacos_config.py
from __future__ import annotations

import json
import threading
from typing import Any, Callable, Dict, Optional, Tuple, Type, TypeVar

import nacos
import yaml
from loguru import logger

from app import settings

T = TypeVar("T")

# ---------------------------
# 线程安全运行时配置仓库
# ---------------------------
class RuntimeConfig:
    """保存 Nacos 配置原文和解析结果；解析失败时保留上一版生效数据。"""
    def __init__(self):
        self._lock = threading.RLock()
        self._raw: Optional[str] = None
        self._data: Dict[str, Any] = {}
        self._last_good_data: Dict[str, Any] = {}
        self._version: int = 0  # 自增版本号，变更时 +1

    @property
    def version(self) -> int:
        with self._lock:
            return self._version

    def _parse_text(self, text: Optional[str]) -> Dict[str, Any]:
        if not text:
            return {}
        # YAML 优先；不行再试 JSON
        try:
            obj = yaml.safe_load(text)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
        return {}

    def update_from_text(self, text: Optional[str]) -> Tuple[int, Dict[str, Any]]:
        """
        更新配置。若解析失败：沿用 last_good_data（保持服务稳定），但仍增加版本号，raw 会更新。
        返回 (version, current_data_copy)
        """
        with self._lock:
            self._raw = text
            parsed = self._parse_text(text)
            if parsed:
                self._data = parsed
                self._last_good_data = parsed
            else:
                # 解析失败则沿用上一版生效数据
                self._data = self._last_good_data
            self._version += 1
            return self._version, self._data.copy()

    def snapshot(self, include_raw: bool = True) -> Dict[str, Any]:
        with self._lock:
            snap = {
                "version": self._version,
                "data": self._data.copy(),
            }
            if include_raw:
                snap["raw"] = self._raw
            return snap

# 单例
runtime_config = RuntimeConfig()


# ---------------------------
# 订阅者（配置变更广播）
# ---------------------------
_subscribers: list[Callable[[dict, int], None]] = []

def subscribe(callback: Callable[[dict, int], None]) -> None:
    """
    订阅配置变更。回调签名：callback(parsed_dict, version)
    注意：回调应快速返回；重操作请投递到后台任务。
    """
    _subscribers.append(callback)

def unsubscribe(callback: Callable[[dict, int], None]) -> None:
    try:
        _subscribers.remove(callback)
    except ValueError:
        pass

def _notify_subscribers(parsed: dict, version: int) -> None:
    for cb in list(_subscribers):
        try:
            cb(parsed, version)
        except Exception as e:
            logger.warning(f"[ConfigSubscriber] callback error: {e}")


# ---------------------------
# Nacos 初始化 & 监听
# ---------------------------
def _on_config_change(args):
    """Nacos 回调（add_listener / add_config_watcher 的 args 兼容 dict）。"""
    data_id = args.get("dataId")
    group = args.get("group")
    content = args.get("content")
    ver, parsed = runtime_config.update_from_text(content)
    logger.info(
        f"[Nacos][ConfigChanged] dataId={data_id}, group={group}, version={ver}, keys={list(parsed.keys())}"
    )
    _notify_subscribers(parsed, ver)

def _register_watcher(client: nacos.NacosClient):
    """兼容不同 SDK 版本的监听 API。"""
    if hasattr(client, "add_config_watcher"):
        client.add_config_watcher(settings.NACOS_DATA_ID, settings.NACOS_GROUP, _on_config_change)
    else:
        client.add_listener(settings.NACOS_DATA_ID, settings.NACOS_GROUP, _on_config_change)

def _unregister_watcher(client: nacos.NacosClient):
    """有的 SDK 支持移除；没有就忽略。"""
    try:
        if hasattr(client, "remove_config_watcher"):
            client.remove_config_watcher(settings.NACOS_DATA_ID, settings.NACOS_GROUP, _on_config_change)
        elif hasattr(client, "remove_listener"):
            client.remove_listener(settings.NACOS_DATA_ID, settings.NACOS_GROUP, _on_config_change)
    except Exception as e:
        logger.warning(f"[Nacos] remove watcher failed: {e}")

def init_nacos_config() -> nacos.NacosClient:
    """
    初始化 Nacos：创建客户端 → 拉取一次配置 → 注册监听 → 广播一次。
    返回 client 实例，便于在 lifespan 里存放以便关闭时做清理。
    """
    client = nacos.NacosClient(
        server_addresses=settings.NACOS_SERVER_ADDR,
        namespace=settings.NACOS_NAMESPACE,
        username=settings.NACOS_USERNAME or None,
        password=settings.NACOS_PASSWORD or None,
    )

    # 启动时拉一次
    content = client.get_config(settings.NACOS_DATA_ID, settings.NACOS_GROUP)

    if not content:
        raise RuntimeError("Failed to load Nacos config")

    ver, parsed = runtime_config.update_from_text(content)
    logger.info(
        f"[Nacos][ConfigLoaded] dataId={settings.NACOS_DATA_ID}, group={settings.NACOS_GROUP}, "
        f"version={ver}, keys={list(parsed.keys())}"
    )

    # 注册监听
    _register_watcher(client)
    logger.info("[Nacos] Config watcher/listener registered.")

    # 广播一次初始配置
    _notify_subscribers(parsed, ver)
    return client

def stop_nacos_config(client: Optional[nacos.NacosClient]):
    """关闭时的清理：移除监听。"""
    if not client:
        return
    _unregister_watcher(client)
    # 某些实现可能还有 close()，若有可在此调用：
    # try: client.close() except: pass


# ---------------------------
# 读取工具
# ---------------------------
def _dig(d: dict, path: str) -> Any:
    """点号路径取值：a.b.c"""
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur

def get_config_snapshot(include_raw: bool = True) -> Dict[str, Any]:
    """给 HTTP 层用的快照视图。"""
    return runtime_config.snapshot(include_raw=include_raw)

def get_value(path: str, default: T | None = None, cast: Callable[[Any], T] | None = None) -> T | Any | None:
    """
    读取单个键（点号路径），支持默认值与类型转换：
    - path: 'a.b.c'
    - default: 找不到时返回
    - cast: 类型转换函数，如 int/float/bool 或自定义 callable
    """
    snap = runtime_config.snapshot(include_raw=False)
    val = _dig(snap["data"], path)
    if val is None:
        return default
    if cast:
        try:
            return cast(val)
        except Exception:
            return default
    return val

def get_section(path: str) -> dict:
    """读取一个 section（dict），不存在返回 {}"""
    snap = runtime_config.snapshot(include_raw=False)
    val = _dig(snap["data"], path)
    return val if isinstance(val, dict) else {}

# ---------------------------
# 强类型读取（Pydantic）
# ---------------------------
_cache: dict[tuple[type, Optional[str]], tuple[int, Any]] = {}

def load_typed(model: Type[T], section: Optional[str] = None, use_cache: bool = True) -> T:
    """
    用 Pydantic 模型解析当前配置。
    - section: 仅解析某个 path（如 'db'）；缺省解析全量。
    - use_cache: 同一版本不重复解析。
    """
    from pydantic import BaseModel  # 延迟导入，避免强依赖

    if not issubclass(model, BaseModel):
        raise TypeError("model must be a pydantic BaseModel subclass")

    ver = runtime_config.version
    key = (model, section)

    if use_cache and key in _cache:
        cached_ver, cached_obj = _cache[key]
        if cached_ver == ver:
            return cached_obj  # type: ignore[return-value]

    data = get_section(section) if section else runtime_config.snapshot(include_raw=False)["data"]
    obj: T = model.model_validate(data)  # type: ignore[assignment]
    if use_cache:
        _cache[key] = (ver, obj)
    return obj
