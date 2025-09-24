FROM python:3.13-slim

ENV PDM_USE_VENV=0 \
    PDM_PEP582=0 \
    TZ=Asia/Shanghai

WORKDIR /data

COPY . .

RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    ln -snf "/usr/share/zoneinfo/$TZ" /etc/localtime && \
    echo "$TZ" > /etc/timezone && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -U pip pdm && \
    pdm lock --check && \
    pdm install --prod --no-editable

ENTRYPOINT ["sh", "-c", "pdm run start"]