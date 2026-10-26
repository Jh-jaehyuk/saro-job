"""Tests for ARQ WorkerSettings registration.

Note: these tests import ``app.tasks.ping`` from the sibling ``apps/api``
workspace package (``saro-job-api``). They will only pass after
``uv sync`` at the repo root has installed both workspace members
editable and ``apps/api`` has scaffolded ``app/tasks/ping.py``.
"""

import pytest
from app.core.config import get_settings
from app.core.sse import RedisProgressPublisher
from app.services.llm import OpenAIClient
from app.services.pdf import PdfplumberExtractor
from app.tasks.ping import ping
from app.tasks.process_resume import process_resume
from worker import WorkerSettings, on_startup


def test_worker_settings_registers_ping() -> None:
    assert ping in WorkerSettings.functions


def test_worker_settings_registers_process_resume() -> None:
    assert process_resume in WorkerSettings.functions


def test_worker_settings_has_queue_name() -> None:
    assert WorkerSettings.queue_name == "saro-job:default"


async def test_on_startup_wires_pdfplumber_extractor() -> None:
    ctx: dict[str, object] = {}
    await on_startup(ctx)
    assert isinstance(ctx["pdf"], PdfplumberExtractor)


async def test_on_startup_wires_redis_progress_publisher() -> None:
    ctx: dict[str, object] = {}
    await on_startup(ctx)
    assert isinstance(ctx["publisher"], RedisProgressPublisher)


async def test_on_startup_wires_openai_client_when_key_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    get_settings.cache_clear()
    try:
        ctx: dict[str, object] = {}
        await on_startup(ctx)
        assert isinstance(ctx["llm"], OpenAIClient)
    finally:
        get_settings.cache_clear()
