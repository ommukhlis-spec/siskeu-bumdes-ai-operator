FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run injects $PORT at runtime; fall back to 8080 for local docker runs.
ENV PORT=8080
EXPOSE 8080

# Shell form with `exec` so $PORT expands at runtime AND uvicorn becomes PID 1
# (so SIGTERM from Cloud Run is delivered correctly during revision shutdown).
# --proxy-headers / --forwarded-allow-ips="*" lets uvicorn trust X-Forwarded-*
# from Cloud Run's front-end proxy.
CMD exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8080} \
    --workers 1 \
    --proxy-headers \
    --forwarded-allow-ips="*"
