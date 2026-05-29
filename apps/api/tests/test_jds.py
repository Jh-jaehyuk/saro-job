"""JD 라우터 통합 테스트. conftest의 truncate + 인증 헬퍼 사용."""

from fastapi.testclient import TestClient

from .conftest import authenticate, login


def test_create_jd_unauthenticated_returns_401(client: TestClient) -> None:
    resp = client.post("/jds", json={"title": "x", "raw_text": "y"})
    assert resp.status_code == 401


def test_create_jd_returns_201_with_org_id(client: TestClient) -> None:
    user = authenticate(client, "hr@example.com")
    resp = client.post("/jds", json={"title": "백엔드 엔지니어", "raw_text": "요구사항..."})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "백엔드 엔지니어"
    assert body["org_id"] == user["org_id"]
    assert body["requirements_json"] == {}


def test_list_jds_only_returns_own_org(client: TestClient) -> None:
    authenticate(client, "a@example.com")
    client.post("/jds", json={"title": "A의 JD", "raw_text": "..."})

    authenticate(client, "b@example.com")  # B로 전환
    assert client.get("/jds").json() == []

    login(client, "a@example.com")  # A로 복귀
    assert [jd["title"] for jd in client.get("/jds").json()] == ["A의 JD"]


def test_get_jd_detail_and_cross_org_404(client: TestClient) -> None:
    authenticate(client, "a@example.com")
    created = client.post("/jds", json={"title": "A의 JD", "raw_text": "..."}).json()
    jd_id = created["id"]
    assert client.get(f"/jds/{jd_id}").status_code == 200

    authenticate(client, "b@example.com")  # 타 org으로 전환
    cross = client.get(f"/jds/{jd_id}")
    assert cross.status_code == 404
    assert cross.json()["error"]["code"] == "JD_NOT_FOUND"
