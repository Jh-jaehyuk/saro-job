###############################################################################
# saro-job worker — multi-stage build
###############################################################################

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv

RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy workspace root + both workspace members (api needed because worker
# depends on saro-job-api via workspace source).
COPY pyproject.toml uv.lock* ./
COPY apps/api ./apps/api
COPY apps/worker ./apps/worker

RUN uv sync --frozen --no-dev --package saro-job-worker

###############################################################################
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/apps/api /app/apps/api
COPY --from=builder /app/apps/worker/worker.py /app/worker.py

CMD ["arq", "worker.WorkerSettings"]
