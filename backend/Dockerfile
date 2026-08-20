# Dockerfile backend — multi-stage
FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir build hatchling
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels .


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY alembic ./alembic
COPY alembic.ini ./
COPY src ./src

RUN mkdir -p /app/generated-servers

ENV GENERATED_SERVERS_DIR=/app/generated-servers

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "mcpgen.api.main:app", "--host", "0.0.0.0", "--port", "8000"]