"""Tests for ARQ WorkerSettings registration.

Note: these tests import ``app.tasks.ping`` from the sibling ``apps/api``
workspace package (``saro-job-api``). They will only pass after
``uv sync`` at the repo root has installed both workspace members
editable and ``apps/api`` has scaffolded ``app/tasks/ping.py``.
"""

from app.tasks.ping import ping
from worker import WorkerSettings


def test_worker_settings_registers_ping() -> None:
    assert ping in WorkerSettings.functions


def test_worker_settings_has_queue_name() -> None:
    assert WorkerSettings.queue_name == "saro-job:default"
