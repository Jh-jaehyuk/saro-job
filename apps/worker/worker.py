"""ARQ worker entrypoint for saro-job background tasks.

Run locally with::

    uv run arq worker.WorkerSettings

The :class:`WorkerSettings` class is the ARQ convention for declaring
registered job functions, the queue name, and the Redis connection.

이 워커는 `process_resume` 잡을 등록하고 PDF 어댑터(`PdfplumberExtractor`)를 ctx에
주입한다. LLMClient는 아직 placeholder이므로, 워커는 parsed 단계까지 처리한 뒤
analyzed 단계에서 NotImplementedError로 실패한다 — OpenAIClient PR에서 LLM
placeholder만 교체하면 end-to-end가 완성된다.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, ClassVar

from app.core.config import get_settings
from app.core.db import AsyncSessionLocal
from app.core.queue import QUEUE_NAME
from app.core.sse import NoopProgressPublisher
from app.schemas.llm import LlmUsage
from app.services.pdf import PdfplumberExtractor
from app.services.storage import S3CompatStorage
from app.tasks.ping import ping
from app.tasks.process_resume import process_resume
from arq.connections import RedisSettings
from pydantic import BaseModel


class _NotImplementedLLMClient:
    """어댑터 PR 전까지 자리만 차지하는 스텁. 호출 시 명확히 실패."""

    async def embed(self, text: str) -> tuple[list[float], LlmUsage]:
        raise NotImplementedError("OpenAIClient not yet wired — adapter PR pending")

    async def structured_completion(
        self, *, purpose: str, system: str, user: str, schema: type[BaseModel]
    ) -> tuple[BaseModel, LlmUsage]:
        raise NotImplementedError("OpenAIClient not yet wired — adapter PR pending")


async def on_startup(ctx: dict[str, Any]) -> None:
    """ARQ 워커 시작 시 ports를 ctx에 주입(composition root)."""
    settings = get_settings()
    ctx["session_factory"] = AsyncSessionLocal
    ctx["storage"] = S3CompatStorage(settings)
    ctx["publisher"] = NoopProgressPublisher()
    ctx["pdf"] = PdfplumberExtractor()
    ctx["llm"] = _NotImplementedLLMClient()


class WorkerSettings:
    """ARQ worker entrypoint. Run: ``uv run arq worker.WorkerSettings``."""

    functions: ClassVar[list[Callable[..., Awaitable[Any]]]] = [ping, process_resume]
    queue_name: ClassVar[str] = QUEUE_NAME
    redis_settings: ClassVar[RedisSettings] = RedisSettings.from_dsn(get_settings().redis_url)
    on_startup: ClassVar[Callable[[dict[str, Any]], Awaitable[None]]] = on_startup
