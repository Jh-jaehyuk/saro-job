"""ARQ worker entrypoint for saro-job background tasks.

Run locally with::

    uv run arq worker.WorkerSettings

The :class:`WorkerSettings` class is the ARQ convention for declaring
registered job functions, the queue name, and the Redis connection.
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from typing import Any, ClassVar

from app.tasks.ping import ping
from arq.connections import RedisSettings


class WorkerSettings:
    """ARQ worker entrypoint. Run: ``uv run arq worker.WorkerSettings``."""

    functions: ClassVar[list[Callable[..., Awaitable[Any]]]] = [ping]
    queue_name: ClassVar[str] = "saro-job:default"
    redis_settings: ClassVar[RedisSettings] = RedisSettings.from_dsn(
        os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    )
