import time

from importlib.metadata import version as pkg_version, PackageNotFoundError
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from loguru import logger

from app import settings
from app.nacos_config import init_nacos_config, stop_nacos_config, get_config_snapshot
from app.nacos_registry import BasicNacosRegistrar
from src.utils.logging import logging_config

logging_config()

def _get_app_version() -> str:
    v = settings.APP_VERSION
    if v:
        return v
    try:
        # 如果你的项目作为包安装，写你自己的包名；否则用默认
        return pkg_version("nacos-fastapi-example")
    except PackageNotFoundError:
        return "0.1.0"

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Nacos 配置监听 & 服务注册（同步）
    nacos_config_client = init_nacos_config()
    naming_client = await BasicNacosRegistrar.register(service_name=settings.SERVICE_NAME, port=settings.APP_PORT, enabled=True)

    try:
        yield
    finally:
        try:
            stop_nacos_config(nacos_config_client)
        except Exception as e:
            logger.warning(f"Nacos remove watcher failed: {e}")
        try:
            await BasicNacosRegistrar.deregister(naming_client, service_name=settings.SERVICE_NAME, port=settings.APP_PORT)
        except Exception as e:
            logger.warning(f"Nacos deregister failed: {e}")

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    from src.utils.trace import new_trace_id, set_trace_id
    # 1) 读取或生成 trace_id
    trace_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID") or new_trace_id()
    set_trace_id(trace_id)

    start = time.time()
    response = await call_next(request)

    # 2) 回写响应头，便于前后端/灰度网关观测
    response.headers["X-Request-ID"] = trace_id

    # 3) 你的访问日志里会自动带 trace_id（因为 patcher 已经设置了）
    process_time = time.time() - start
    client_ip = request.client.host if request.client else "unknown"
    client_port = request.client.port if request.client else "unknown"
    logger.info(f"{client_ip}:{client_port} \"{request.method} {request.url.path} HTTP/1.1\" "
                f"{response.status_code} - {process_time:.4f}s")

    return response

@app.get("/health", operation_id="health")
async def health():
    logger.info("health check")
    return {"ok": True, "env": settings.APP_ENV}

@app.get("/config/nacos", operation_id="nacos_config")
async def nacos_config():
    """打印当前所有配置：环境 + Nacos 动态解析 + 原文（可去掉 raw）"""
    nacos_snapshot = get_config_snapshot()
    return {"nacos": nacos_snapshot}