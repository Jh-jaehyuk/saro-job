"""S3CompatStorage 유닛 테스트.

boto3 presigning은 로컬 HMAC 서명이라 네트워크/MinIO 없이 동작한다. URL 구조와
키 규칙만 검증하고, 실제 PUT/GET 왕복은 파이프라인 PR의 통합 테스트로 미룬다.
"""

import uuid
from urllib.parse import parse_qs, urlparse

import pytest
from app.core.config import Settings
from app.services.storage import S3CompatStorage


@pytest.fixture
def storage() -> S3CompatStorage:
    settings = Settings(
        s3_endpoint_url="http://localhost:9000",
        s3_region="auto",
        s3_access_key_id="testkey",
        s3_secret_access_key="testsecret",
        s3_bucket="test-bucket",
    )
    return S3CompatStorage(settings)


def test_build_resume_key(storage: S3CompatStorage) -> None:
    org_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    resume_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    assert storage.build_resume_key(org_id, resume_id) == (
        "org_11111111-1111-1111-1111-111111111111/resume_22222222-2222-2222-2222-222222222222.pdf"
    )


def test_generate_upload_url_contains_bucket_key_and_signature(
    storage: S3CompatStorage,
) -> None:
    url = storage.generate_upload_url("org_a/resume_b.pdf")
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    assert "test-bucket" in url
    assert "org_a/resume_b.pdf" in url
    assert "X-Amz-Signature" in qs
    assert qs["X-Amz-Expires"] == ["3600"]


def test_generate_download_url_distinct_from_upload(storage: S3CompatStorage) -> None:
    key = "org_a/resume_b.pdf"
    upload = storage.generate_upload_url(key)
    download = storage.generate_download_url(key)
    # presigned URL은 HTTP 메서드별 서명이 달라 동일하지 않다.
    assert upload != download
    assert "X-Amz-Signature" in parse_qs(urlparse(download).query)
