"""Match 조회 라우터 통합 테스트.

파이프라인이 아직 Match를 만들지 않으므로, 테스트가 DB에 직접 Match/Question을
삽입한 뒤 HTTP 조회를 검증한다.
"""

import asyncio
import uuid

from app.core.config import get_settings
from app.models.interview_question import InterviewQuestion
from app.models.match import Match
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from .conftest import authenticate


def _insert_match(jd_id: str, resume_id: str, *, grade: str = "상") -> str:
    async def _run() -> str:
        engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
        try:
            async with AsyncSession(engine) as s:
                match = Match(
                    jd_id=uuid.UUID(jd_id),
                    resume_id=uuid.UUID(resume_id),
                    overall_score=0.9,
                    category_scores_json={},
                    grade=grade,
                    matched_keywords_json=[],
                    missing_keywords_json=[],
                )
                s.add(match)
                await s.flush()
                match_id = match.id  # commit 후엔 expire되어 접근 시 IO 발생.
                s.add(
                    InterviewQuestion(
                        match_id=match_id,
                        question="가장 큰 기술적 도전은?",
                        question_type="technical",
                        order=1,
                    )
                )
                await s.commit()
                return str(match_id)
        finally:
            await engine.dispose()

    return asyncio.run(_run())


def _seed_jd_and_resume(client: TestClient) -> tuple[str, str]:
    jd_id = client.post("/jds", json={"title": "JD", "raw_text": "..."}).json()["id"]
    resume_id = client.post("/resumes/upload-url", json={"filename": "c.pdf"}).json()["resume_id"]
    return jd_id, resume_id


def test_list_matches_empty_for_new_jd(client: TestClient) -> None:
    authenticate(client, "hr@example.com")
    jd_id, _ = _seed_jd_and_resume(client)
    resp = client.get(f"/jds/{jd_id}/matches")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_match_and_questions(client: TestClient) -> None:
    authenticate(client, "hr@example.com")
    jd_id, resume_id = _seed_jd_and_resume(client)
    match_id = _insert_match(jd_id, resume_id)

    listed = client.get(f"/jds/{jd_id}/matches").json()
    assert [m["id"] for m in listed] == [match_id]
    assert listed[0]["grade"] == "상"

    detail = client.get(f"/matches/{match_id}")
    assert detail.status_code == 200
    assert detail.json()["resume_id"] == resume_id

    questions = client.get(f"/matches/{match_id}/questions").json()
    assert [q["question_type"] for q in questions] == ["technical"]


def test_match_cross_org_returns_404(client: TestClient) -> None:
    authenticate(client, "a@example.com")
    jd_id, resume_id = _seed_jd_and_resume(client)
    match_id = _insert_match(jd_id, resume_id)

    authenticate(client, "b@example.com")  # 타 org으로 전환
    assert client.get(f"/matches/{match_id}").status_code == 404
    assert client.get(f"/jds/{jd_id}/matches").status_code == 404
