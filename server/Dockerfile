FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/server:/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        coinor-cbc \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY server/requirements.txt ./server/requirements.txt
RUN pip install -r ./server/requirements.txt

COPY server/ ./server/
COPY shared/ ./shared/

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health > /dev/null || exit 1

CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "8000"]