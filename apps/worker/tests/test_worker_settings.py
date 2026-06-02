"""Tests for ARQ WorkerSettings registration.

Note: these tests import ``app.tasks.ping`` from the sibling ``apps/api``
workspace package (``saro-job-api``). They will only pass after
``uv sync`` at the repo root has installed both workspace members
editable and ``apps/api`` has scaffolded ``app/tasks/ping.py``.
"""

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
