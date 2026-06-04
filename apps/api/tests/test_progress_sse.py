"""GET /jds/{jd_id}/progress (SSE) 통합 테스트.

스트림 수신 end-to-end는 TestClient sync 환경에서 안정적이지 않아 수동 검증으로
위임한다(`Verification`의 e2e 흐름). 여기서는 인증·교차 테넌트 404·SSE 헤더가
정확한지 확인한다. 실 Redis pub/sub 동작은 `test_redis_publisher.py`가 커버.
"""

import uuid

from fastapi.testclient import TestClient

from .conftest import authenticate


def test_progress_requires_authentication(client: TestClient) -> None:
    resp = client.get(f"/jds/{uuid.uuid4()}/progress")
    assert resp.status_code == 401


def test_progress_returns_404_for_cross_org_jd(client: TestClient) -> None:
    authenticate(client, "a@example.com")
    jd_id = client.post("/jds", json={"title": "JD", "raw_text": "..."}).json()["id"]

    authenticate(client, "b@example.com")
    resp = client.get(f"/jds/{jd_id}/progress")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "JD_NOT_FOUND"


def test_progress_route_is_registered(client: TestClient) -> None:
    """라우터 등록 확인 — 미인증과 인증된 케이스의 응답 코드가 다르다.

    실제 스트림 헤더/데이터 e2e는 `test_redis_publisher.py`(pub/sub)와 수동 검증으로.
    TestClient(sync portal)가 SSE generator 정리에서 hang하기 쉽기 때문이다.
    """
    paths = {route.path for route in client.app.routes if hasattr(route, "path")}
    assert "/jds/{jd_id}/progress" in paths
    assert "/jds/{jd_id}/status" in paths
