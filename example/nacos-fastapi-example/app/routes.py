from fastapi import APIRouter
from loguru import logger
from app import settings
from app.nacos_config import get_config_snapshot, get_value

router = APIRouter()

@router.get("/", operation_id="index")
async def root() -> dict[str, str]:
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }

@router.get("/health", operation_id="health")
async def health():
    logger.info("health check")
    return {"ok": True, "env": settings.APP_ENV}

@router.get("/config/nacos", operation_id="nacos_config")
async def nacos_config():
    """打印当前所有配置：环境 + Nacos 动态解析 + 原文（可去掉 raw）"""
    nacos_snapshot = get_config_snapshot()
    return {"nacos": nacos_snapshot}

@router.get("/config/get-mysql-username", operation_id="nacos_config_get_mysql_username")
async def nacos_config_get_mysql_username():
    username = get_value("database.mysql.username")
    return {"database.mysql.username": username}