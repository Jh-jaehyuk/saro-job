# saro-job-worker

ARQ background worker for saro-job. Consumes jobs from the `saro-job:default`
Redis queue and dispatches to task functions registered on `WorkerSettings`.

## Run locally

```bash
uv run arq worker.WorkerSettings
```

Requires `REDIS_URL` (defaults to `redis://localhost:6379/0`).

## Module boundary

Per [AGENTS.md §3](../../AGENTS.md), this app may import only from
`apps/api/app/tasks/*` and `apps/api/app/services/*` — never from routers.
