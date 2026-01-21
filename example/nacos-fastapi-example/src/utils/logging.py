import sys

from loguru import logger

from app import settings
from src.utils.trace import get_trace_id

# 允许透传到 JSON 的额外字段白名单（可按需增减）
_EXTRA_ALLOWLIST = {
    "evt",  # 事件名，如 "http.access" / "kafka.consume"
    # HTTP 访问
    "method", "path", "status", "dur_ms", "ip",
    # Kafka
    "topic", "partition", "offset",
    # 你自己常用的
    "user_id", "job_id",
}


def logging_config():
    logger.remove()

    # 给每条日志打上 trace_id
    def _patch(record):
        record["extra"]["trace_id"] = record["extra"].get("trace_id") or get_trace_id() or "-"

    logger.configure(patcher=_patch)

    log_level = settings.APP_LOG_LEVEL.upper()

    # 确定日志格式
    if settings.APP_LOG_FORMAT.lower() == "json":
        # JSON格式 - 使用简单的JSON格式字符串
        log_format = '{{"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", "level": "{level}", "trace": "{extra[trace_id]}", "name": "{name}", "function": "{function}", "line": {line}, "message": "{message}"}}'
    else:
        # 文本格式
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | trace=<cyan>{extra[trace_id]}</cyan> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    # 控制台
    logger.add(
        sys.stdout,
        level=log_level,
        format=log_format,
        enqueue=True,
    )

    # 文件（如配置）
    if settings.APP_LOG_PATH:
        rotation = settings.APP_LOG_ROTATION
        if isinstance(rotation, str) and rotation.endswith(("KB", "MB", "GB")):
            unit = rotation[-2:];
            num = int(rotation[:-2]);
            factor = {"KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}[unit]
            rotation = num * factor
        logger.add(
            settings.APP_LOG_PATH,
            level=log_level,
            format=log_format,
            rotation=rotation,
            retention=settings.APP_LOG_RETENTION,
            compression="gz",
            encoding="utf-8",
            enqueue=True,
        )

    logger.info("logging configured")
