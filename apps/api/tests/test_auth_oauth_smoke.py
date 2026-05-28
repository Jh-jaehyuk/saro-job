"""Google OAuth 라우터 smoke 테스트.

기본 .env에는 Google OAuth 키가 비어 있어 라우터가 등록되지 않는다
(`google_oauth_client is None`). 이 테스트는 키 주입 → 앱 재구성 → `/auth/google/authorize`
경로가 등록되어 authorization_url을 돌려주는지만 검증한다. 실제 Google 호출은
하지 않는다.
"""

import importlib

from fastapi.testclient import TestClient


def test_google_oauth_router_registers_when_keys_present(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-client-secret")

    # Settings는 lru_cache → 캐시 비우고 모듈 재로딩.
    from app import main as main_mod
    from app.core import auth as auth_mod
    from app.core import config as config_mod
    from app.routers import auth as routers_auth

    config_mod.get_settings.cache_clear()
    importlib.reload(auth_mod)
    importlib.reload(routers_auth)
    importlib.reload(main_mod)

    try:
        client = TestClient(main_mod.app)
        resp = client.get("/auth/google/authorize", follow_redirects=False)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "authorization_url" in body
        assert body["authorization_url"].startswith("https://accounts.google.com/o/oauth2/v2/auth")
    finally:
        # 다른 테스트에 영향이 가지 않도록 원상복구.
        monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_ID", raising=False)
        monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_SECRET", raising=False)
        config_mod.get_settings.cache_clear()
        importlib.reload(auth_mod)
        importlib.reload(routers_auth)
        importlib.reload(main_mod)
