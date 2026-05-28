"""Auth flow tests — register, login, /users/me, organization auto-create.

로컬 postgres(`docker compose up -d postgres`)에 의존한다. 각 테스트 시작 시
users/organizations 테이블을 truncate하여 격리한다.
"""

import asyncio

import pytest
from app.core.db import async_engine
from fastapi.testclient import TestClient
from sqlalchemy import text


@pytest.fixture(autouse=True)
def _reset_tables() -> None:
    """매 테스트 직전에 users/organizations를 truncate."""

    async def _truncate() -> None:
        async with async_engine.begin() as conn:
            await conn.execute(text("TRUNCATE TABLE users, organizations RESTART IDENTITY CASCADE"))
        # 매 테스트가 새 이벤트 루프를 만들어 asyncio.run 한다. 이전 루프에 묶인
        # 연결이 풀에 남으면 다음 루프에서 "Event loop is closed" 오류가 난다.
        await async_engine.dispose()

    asyncio.run(_truncate())


def test_users_me_unauthenticated_returns_401(client: TestClient) -> None:
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_register_then_me_returns_user_with_org(client: TestClient) -> None:
    register = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert register.status_code == 201, register.text
    body = register.json()
    assert body["email"] == "alice@example.com"
    assert body.get("org_id") is not None  # on_after_register 훅이 채움

    login = client.post(
        "/auth/cookie/login",
        data={"username": "alice@example.com", "password": "password123"},
    )
    assert login.status_code == 204, login.text
    assert "sarojob_session" in login.cookies

    me = client.get("/users/me", cookies=login.cookies)
    assert me.status_code == 200
    me_body = me.json()
    assert me_body["email"] == "alice@example.com"
    assert me_body["org_id"] is not None
