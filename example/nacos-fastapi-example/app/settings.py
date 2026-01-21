import os
from pathlib import Path
from dotenv import load_dotenv

# 本地开发加载 .env（生产由容器/K8s 注入）
load_dotenv(dotenv_path=Path(".") / ".env", override=False)

APP_NAME = os.getenv("APP_NAME", "nacos-fastapi-example")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = os.getenv("APP_PORT", "8000")
APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL")
APP_LOG_PATH = os.getenv("APP_LOG_PATH")
APP_LOG_FORMAT = os.getenv("APP_LOG_FORMAT")
APP_LOG_ROTATION = os.getenv("APP_LOG_ROTATION")
APP_LOG_RETENTION = os.getenv("APP_LOG_RETENTION")
APP_VERSION = os.getenv("APP_VERSION")
APP_ENV = os.getenv("APP_ENV", "dev")
APP_WORKERS = os.getenv("APP_WORKERS")
DEBUG = APP_LOG_LEVEL == "debug"

# Nacos
NACOS_SERVER_ADDR = os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848")
NACOS_NAMESPACE = os.getenv("NACOS_NAMESPACE", "public")
NACOS_USERNAME = os.getenv("NACOS_USERNAME", "")
NACOS_PASSWORD = os.getenv("NACOS_PASSWORD", "")

# Nacos 配置（ConfigService）
NACOS_DATA_ID = os.getenv("NACOS_DATA_ID", "nacos-fastapi-example.yaml")
NACOS_GROUP = os.getenv("NACOS_GROUP", "DEFAULT_GROUP")

# Nacos 注册（NamingService）
SERVICE_NAME = os.getenv("SERVICE_NAME", "nacos-fastapi-example")
SERVICE_GROUP = os.getenv("SERVICE_GROUP", "DEFAULT_GROUP")
SERVICE_CLUSTER = os.getenv("SERVICE_CLUSTER", "DEFAULT")
