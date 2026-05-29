"""Auth flow tests — register, login, /users/me, organization auto-create.

로컬 postgres(`docker compose up -d postgres`)에 의존한다. 테이블 격리는 conftest의
autouse `_reset_tables` 픽스처가 담당한다.
"""

from fastapi.testclient import TestClient


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
