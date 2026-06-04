"""GET /jds/{jd_id}/status 통합 테스트.

SSE 재연결 시 클라이언트가 호출하여 현재 잡 상태 1회 동기화한다(§6.3).
"""

import asyncio
import uuid

from app.core.config import get_settings
from app.models.resume import Resume
from app.models.resume_processing_job import ResumeProcessingJob
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from .conftest import authenticate


def _seed_job(jd_id: str, org_id: str) -> None:
    async def _run() -> None:
        engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
        try:
            async with AsyncSession(engine) as s:
                resume = Resume(
                    org_id=uuid.UUID(org_id),
                    pdf_key=f"org_{org_id}/resume_{uuid.uuid4()}.pdf",
                )
                s.add(resume)
                await s.flush()
                s.add(
                    ResumeProcessingJob(
                        resume_id=resume.id,
                        jd_id=uuid.UUID(jd_id),
                        state="queued",
                        step_state_json={},
                    )
                )
                await s.commit()
        finally:
            await engine.dispose()

    asyncio.run(_run())


def test_status_requires_authentication(client: TestClient) -> None:
    resp = client.get(f"/jds/{uuid.uuid4()}/status")
    assert resp.status_code == 401


def test_status_returns_404_for_cross_org_jd(client: TestClient) -> None:
    authenticate(client, "a@example.com")
    jd_id = client.post("/jds", json={"title": "JD", "raw_text": "..."}).json()["id"]

    authenticate(client, "b@example.com")
    resp = client.get(f"/jds/{jd_id}/status")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "JD_NOT_FOUND"


def test_status_lists_processing_jobs(client: TestClient) -> None:
    user = authenticate(client, "hr@example.com")
    jd_id = client.post("/jds", json={"title": "JD", "raw_text": "..."}).json()["id"]
    _seed_job(jd_id, user["org_id"])

    resp = client.get(f"/jds/{jd_id}/status")
    assert resp.status_code == 200
    jobs = resp.json()
    assert len(jobs) == 1
    assert jobs[0]["state"] == "queued"
    assert jobs[0]["jd_id"] == jd_id
