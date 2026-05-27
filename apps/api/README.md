# saro-job-api

FastAPI backend for saro-job — handles HTTP endpoints (resumes, jobs, matches, interviews), delegates long-running work to the ARQ worker, and persists state to Postgres (pgvector) and S3-compatible storage.

## Run locally

```bash
uv sync
uv run uvicorn app.main:app --reload --app-dir apps/api
```

## Test

```bash
uv run pytest apps/api/tests -v
uv run mypy --strict apps/api/app
uv run ruff check apps/api
```

See repo root [`AGENTS.md`](../../AGENTS.md) for architecture, coding rules, and boundary contracts.
