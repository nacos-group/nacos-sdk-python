# nacos-fastapi-example

A reference FastAPI service that demonstrates how to integrate [Nacos](https://nacos.io/) for configuration. The project is managed with [PDM](https://pdm.fming.dev/) and targets Python 3.13.

## Features
- FastAPI application with custom lifespan and registers the service to Nacos.
- Runtime configuration syncing from Nacos with YAML/JSON parsing and in-memory cache snapshots.
- Structured logging via Loguru with trace ID propagation utilities (`src/utils`).
- PDM scripts for common workflows (`dev`, `start`, `lint`, `fmt`, `typecheck`, `test`).

## Project Layout
```
app/                FastAPI entrypoints, Nacos integration, settings helper
src/utils/          Logging and trace helpers shared across the app
logs/               Local log output (ignored in Docker image)
.nacos-data/        Local Nacos snapshot storage (ignored in Docker image)
```

## Prerequisites
- Python 3.13
- [PDM](https://pdm.fming.dev/latest/#installation)
- Nacos server **3.x** (tested with 3.0.3) and reachable credentials/namespace (`NACOS_SERVER_ADDR`, `NACOS_USERNAME`, `NACOS_NAMESPACE`, ...)
- Optional: Docker 24+ for containerized deployments

## Preparing Nacos
1. Upload the sample configuration `nacos-fastapi-example.yaml` to the Nacos Config Service.
   - Data ID: `nacos-fastapi-example.yaml`
   - Group: `DEFAULT_GROUP`
   - Namespace: align with `NACOS_NAMESPACE` in your environment
2. Adjust the YAML contents as needed for your runtime (database DSN, feature flags, etc.).
3. Ensure the Nacos HTTP/GRPC endpoints are accessible from where this FastAPI service runs.

## Local Setup
1. Copy the environment example and adjust values for your setup:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies with PDM (a virtualenv will be created automatically if configured):
   ```bash
   pdm install
   ```

## Running the Service
- Development mode with hot reload:
  ```bash
  pdm run dev
  ```
- Production-style single process (relies on the `.env` configuration):
  ```bash
  pdm run start
  ```

The application exposes:
- `GET /health` — lightweight health probe.
- `GET /config/nacos` — current runtime configuration snapshot from Nacos.

## Docker Usage
The repository ships with a `Dockerfile`. Because `.env` is excluded by `.dockerignore`, pass it at runtime.

Build the image:
```bash
docker build -t nacos-fastapi-example:v0.1.0 .
```

Run the container (map ports and supply the `.env` file):
```bash
docker run -d \
  --name nacos-fastapi-example \
  --env-file .env \
  -p 8000:8000 \
  nacos-fastapi-example:v0.1.0
```
Adjust the port mapping if you expose a different `APP_PORT`.

## Notes
- The default `.env.example` enables Nacos registration; ensure the Nacos address and credentials are reachable.
- Logging output lives in `logs/` locally; mount a volume or override `APP_LOG_PATH` if you want to persist logs inside Docker.

## Documentation
For additional context in Chinese, see [README.zh.md](README.zh.md).
