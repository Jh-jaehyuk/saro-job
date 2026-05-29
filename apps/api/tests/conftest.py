"""Shared pytest fixtures for apps/api tests.

로컬 postgres(`docker compose up -d postgres`)에 의존한다. 매 테스트 직전에 모든
도메인 테이블을 truncate하여 격리하고, `get_storage`는 fake로 override하여 라우터
테스트가 boto3 자격증명/네트워크에 의존하지 않게 한다(presign 실동작은
`test_storage.py`가 커버).
"""

import asyncio
import uuid
from collections.abc import Iterator

import pytest
from app.core.config import get_settings
from app.core.db import async_engine
from app.main import app
from app.services.storage import get_storage
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

_TABLES = (
    "users, organizations, job_descriptions, resumes, matches, "
    "interview_questions, resume_processing_jobs, llm_calls"
)


@pytest.fixture(autouse=True)
def _reset_tables() -> None:
    """매 테스트 직전에 모든 도메인 테이블을 truncate(CASCADE)."""

    async def _truncate() -> None:
        # 앱의 글로벌 엔진을 쓰면 이전 테스트 루프에 묶인 풀 커넥션을 재사용해
        # "Event loop is closed"가 난다. NullPool 단발 엔진으로 완전히 격리한다.
        engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
        try:
            async with engine.begin() as conn:
                await conn.execute(text(f"TRUNCATE TABLE {_TABLES} RESTART IDENTITY CASCADE"))
        finally:
            await engine.dispose()
        # 앱 글로벌 엔진 풀도 비운다. 각 테스트의 TestClient는 새 이벤트 루프를
        # 쓰므로, 이전 루프에 묶인 풀 커넥션이 남으면 "attached to a different loop".
        await async_engine.dispose()

    asyncio.run(_truncate())


class _FakeStorage:
    """네트워크 없는 ObjectStorage 더미. 키 규칙은 실제와 동일하게 유지."""

    def build_resume_key(self, org_id: uuid.UUID, resume_id: uuid.UUID) -> str:
        return f"org_{org_id}/resume_{resume_id}.pdf"

    def generate_upload_url(self, key: str, *, expires_in: int = 3600) -> str:
        return f"https://fake-bucket.example/{key}?sig=upload"

    def generate_download_url(self, key: str, *, expires_in: int = 3600) -> str:
        return f"https://fake-bucket.example/{key}?sig=download"


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Fake storage가 주입된 TestClient."""
    app.dependency_overrides[get_storage] = _FakeStorage
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def login(client: TestClient, email: str, password: str = "password123") -> None:
    """기존 사용자로 로그인(쿠키 교체). 교차 테넌트 테스트에서 사용자 전환에 사용."""
    resp = client.post("/auth/cookie/login", data={"username": email, "password": password})
    assert resp.status_code == 204, resp.text


def authenticate(client: TestClient, email: str, password: str = "password123") -> dict:
    """주어진 client로 가입+로그인하고(쿠키 저장됨) user JSON(org_id 포함) 반환.

    교차 테넌트 테스트는 TestClient 2개 대신 단일 client에서 이 함수로 사용자를
    전환한다(TestClient마다 이벤트 루프가 달라 글로벌 엔진 풀과 충돌하기 때문).
    """
    register = client.post("/auth/register", json={"email": email, "password": password})
    assert register.status_code == 201, register.text
    login(client, email, password)
    return register.json()
