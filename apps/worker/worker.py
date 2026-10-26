"""ARQ worker entrypoint for saro-job background tasks.

Run locally with::

    uv run arq worker.WorkerSettings

The :class:`WorkerSettings` class is the ARQ convention for declaring
registered job functions, the queue name, and the Redis connection.

이 워커는 `process_resume` 잡을 등록하고 PDF 어댑터(`PdfplumberExtractor`)와
LLM 어댑터(`OpenAIClient`)를 ctx에 주입한다. `OPENAI_API_KEY`가 비어 있으면 LLM은
placeholder로 남아, 워커는 parsed 단계까지 처리한 뒤 analyzed 단계에서
NotImplementedError로 실패한다.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, ClassVar

import redis.asyncio as aioredis
from app.core.config import get_settings
from app.core.db import AsyncSessionLocal
from app.core.queue import QUEUE_NAME
from app.core.sse import RedisProgressPublisher
from app.schemas.llm import LlmUsage
from app.services.llm import OpenAIClient
from app.services.pdf import PdfplumberExtractor
from app.services.storage import S3CompatStorage
from app.tasks.ping import ping
from app.tasks.process_resume import process_resume
from arq.connections import RedisSettings
from pydantic import BaseModel


class _NotImplementedLLMClient:
    """OPENAI_API_KEY가 없을 때 자리만 차지하는 스텁. 호출 시 명확히 실패."""

    async def embed(self, text: str) -> tuple[list[float], LlmUsage]:
        raise NotImplementedError("OPENAI_API_KEY not set")

    async def structured_completion(
        self, *, purpose: str, system: str, user: str, schema: type[BaseModel]
    ) -> tuple[BaseModel, LlmUsage]:
        raise NotImplementedError("OPENAI_API_KEY not set")


async def on_startup(ctx: dict[str, Any]) -> None:
    """ARQ 워커 시작 시 ports를 ctx에 주입(composition root)."""
    settings = get_settings()
    redis_client = aioredis.from_url(settings.redis_url)  # type: ignore[no-untyped-call]
    ctx["session_factory"] = AsyncSessionLocal
    ctx["storage"] = S3CompatStorage(settings)
    ctx["publisher"] = RedisProgressPublisher(redis_client)
    ctx["pdf"] = PdfplumberExtractor()
    ctx["llm"] = OpenAIClient(settings) if settings.openai_api_key else _NotImplementedLLMClient()
    ctx["_redis"] = redis_client  # 정리용 보관(다음 PR에서 on_shutdown 정리).


class WorkerSettings:
    """ARQ worker entrypoint. Run: ``uv run arq worker.WorkerSettings``."""

    functions: ClassVar[list[Callable[..., Awaitable[Any]]]] = [ping, process_resume]
    queue_name: ClassVar[str] = QUEUE_NAME
    redis_settings: ClassVar[RedisSettings] = RedisSettings.from_dsn(get_settings().redis_url)
    on_startup: ClassVar[Callable[[dict[str, Any]], Awaitable[None]]] = on_startup
