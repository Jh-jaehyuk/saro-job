"""Resume 업로드 라우터 통합 테스트. enqueue는 보류 상태이므로 잡 row만 검증."""

from fastapi.testclient import TestClient

from .conftest import FakeArqPool, authenticate


def _create_jd(client: TestClient) -> str:
    return client.post("/jds", json={"title": "JD", "raw_text": "..."}).json()["id"]


def test_upload_url_creates_resume_with_deterministic_key(client: TestClient) -> None:
    user = authenticate(client, "hr@example.com")
    resp = client.post("/resumes/upload-url", json={"filename": "candidate.pdf"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    resume_id = body["resume_id"]
    # fake storage가 결정적 키 규칙(org_{org}/resume_{id}.pdf)으로 URL 생성.
    assert f"org_{user['org_id']}/resume_{resume_id}.pdf" in body["upload_url"]


def test_finalize_creates_queued_job(client: TestClient) -> None:
    authenticate(client, "hr@example.com")
    jd_id = _create_jd(client)
    resume_id = client.post("/resumes/upload-url", json={"filename": "c.pdf"}).json()["resume_id"]

    resp = client.post(f"/resumes/{resume_id}/finalize", json={"jd_id": jd_id})
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["resume_id"] == resume_id
    assert body["jd_id"] == jd_id
    assert body["state"] == "queued"


def test_finalize_is_idempotent(client: TestClient, arq_pool: FakeArqPool) -> None:
    authenticate(client, "hr@example.com")
    jd_id = _create_jd(client)
    resume_id = client.post("/resumes/upload-url", json={"filename": "c.pdf"}).json()["resume_id"]

    first = client.post(f"/resumes/{resume_id}/finalize", json={"jd_id": jd_id}).json()
    second = client.post(f"/resumes/{resume_id}/finalize", json={"jd_id": jd_id}).json()
    assert first["id"] == second["id"]
    # 큐 적재는 1회만 — 두 번째 finalize는 기존 잡을 반환.
    assert len(arq_pool.calls) == 1


def test_finalize_enqueues_process_resume(client: TestClient, arq_pool: FakeArqPool) -> None:
    authenticate(client, "hr@example.com")
    jd_id = _create_jd(client)
    resume_id = client.post("/resumes/upload-url", json={"filename": "c.pdf"}).json()["resume_id"]

    client.post(f"/resumes/{resume_id}/finalize", json={"jd_id": jd_id})

    assert len(arq_pool.calls) == 1
    function, args, kwargs = arq_pool.calls[0]
    assert function == "process_resume"
    assert args == (resume_id, jd_id)
    assert kwargs["_queue_name"] == "saro-job:default"


def test_finalize_cross_org_resume_returns_404(client: TestClient) -> None:
    authenticate(client, "a@example.com")
    resume_id = client.post("/resumes/upload-url", json={"filename": "c.pdf"}).json()["resume_id"]

    authenticate(client, "b@example.com")  # 타 org으로 전환
    jd_id = _create_jd(client)  # B의 JD
    resp = client.post(f"/resumes/{resume_id}/finalize", json={"jd_id": jd_id})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESUME_NOT_FOUND"


def test_finalize_cross_org_jd_returns_404(client: TestClient) -> None:
    authenticate(client, "a@example.com")
    jd_id = _create_jd(client)  # A의 JD

    authenticate(client, "b@example.com")  # 타 org으로 전환
    resume_id = client.post("/resumes/upload-url", json={"filename": "c.pdf"}).json()[
        "resume_id"
    ]  # B의 resume
    resp = client.post(f"/resumes/{resume_id}/finalize", json={"jd_id": jd_id})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "JD_NOT_FOUND"
