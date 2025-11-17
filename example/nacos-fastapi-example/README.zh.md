# nacos-fastapi-example

一个示例项目，演示如何在 FastAPI 服务中接入 [Nacos](https://nacos.io/) 配置中心与服务发现。项目使用 [PDM](https://pdm.fming.dev/) 管理依赖，目标 Python 3.13。

## 功能亮点
- 自定义 FastAPI lifespan：将服务注册到 Nacos。
- 监听 Nacos 配置，支持 YAML/JSON 解析与内存快照缓存。
- 基于 Loguru 的结构化日志，配合 `src/utils` 下的 trace ID 工具。
- 预置 PDM 脚本：`dev`、`start`、`lint`、`fmt`、`typecheck`、`test` 等。

## 项目结构
```
app/                FastAPI 入口、Nacos 交互、配置加载
src/utils/          通用的日志与链路追踪工具
logs/               本地日志输出目录（镜像构建时会忽略）
nacos-data/         Nacos 本地快照（镜像构建时会忽略）
```

## 环境准备
- Python 3.13
- 已安装 PDM
- **Nacos 3.x**（测试使用 3.0.3），并确保 `NACOS_SERVER_ADDR`、`NACOS_USERNAME`、`NACOS_NAMESPACE` 等可用
- 可选：Docker 24+，用于容器部署

## 准备 Nacos 配置
1. 将仓库根目录的 `nacos-fastapi-example.yaml` 上传到 Nacos 配置中心：
   - Data ID：`nacos-fastapi-example.yaml`
   - Group：`DEFAULT_GROUP`
   - Namespace：与 `.env` 中 `NACOS_NAMESPACE` 保持一致
2. 根据业务需要修改 YAML 内的具体配置（如数据库、特性开关等）。
3. 确保服务部署环境能够访问 Nacos 的 HTTP/GRPC 端口。

## 本地运行
1. 复制环境变量模板并按需修改：
   ```bash
   cp .env.example .env
   ```
2. 安装依赖：
   ```bash
   pdm install
   ```

## 启动方式
- 开发模式（自动重载）：
  ```bash
  pdm run dev
  ```
- 类生产模式（单进程，以 `.env` 为准）：
  ```bash
  pdm run start
  ```

对外接口：
- `GET /health` — 健康检查。
- `GET /config/nacos` — 当前 Nacos 配置快照。

## Docker 使用
仓库提供 `Dockerfile`，`.env` 已由 `.dockerignore` 排除，需要在运行容器时显式注入。

构建镜像：
```bash
docker build -t nacos-fastapi-example:v0.1.0 .
```

启动容器（映射端口并加载 `.env`）：
```bash
docker run -d \
  --name nacos-fastapi-example \
  --env-file .env \
  -p 8000:8000 \
  nacos-fastapi-example:v0.1.0
```
如果使用了其他端口或想持久化日志，可根据需要调整端口映射或挂载卷。

## 额外提示
- `.env.example` 默认开启 Nacos 注册。
- 日志默认写入 `logs/`，在 Docker 环境中请配置卷或修改 `APP_LOG_PATH`。

## 其他语言
英文文档请查看 [README.md](README.md)。
