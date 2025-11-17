from __future__ import annotations

import argparse

from loguru import logger
import uvicorn

from app import settings

def _to_int(v, default=None):
    try:
        if v is None or v == "":
            return default
        return int(str(v).strip())
    except Exception:
        return default

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reload", action="store_true", help="enable auto-reload (dev)")
    args = parser.parse_args()

    host = settings.APP_HOST
    port = _to_int(settings.APP_PORT)
    uvicorn_level = settings.APP_LOG_LEVEL
    raw_workers = settings.APP_WORKERS
    workers = _to_int(raw_workers, 1)
    workers_param = None if args.reload else workers  # reload 与多 worker 不兼容

    logger.info(f"Starting uvicorn: host={host}, port={port}, workers={workers}, log_level={uvicorn_level}, reload={args.reload}")

    # 可选：生产启用 uvloop（安装了才生效）
    if uvicorn_level != "debug":
        try:
            import uvloop, asyncio
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        except Exception:
            pass

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=args.reload,
        log_level=uvicorn_level,
        workers=workers_param
    )


if __name__ == "__main__":
    main()