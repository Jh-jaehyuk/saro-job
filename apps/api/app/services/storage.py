"""ObjectStorage Port + S3 호환 구현(R2/MinIO 공용).

브라우저가 presigned URL로 R2에 직접 PUT/GET 한다(ARCHITECTURE §6.1). 백엔드는
URL 서명만 한다 — presigning은 로컬 HMAC 계산이라 네트워크 호출이 없다.
"""

import uuid
from typing import Protocol

import boto3
from botocore.config import Config

from app.core.config import Settings


class ObjectStorage(Protocol):
    """오브젝트 스토리지 경계. 구현체 교체 가능(R2/MinIO/기타 S3 호환)."""

    def build_resume_key(self, org_id: uuid.UUID, resume_id: uuid.UUID) -> str: ...

    def generate_upload_url(self, key: str, *, expires_in: int = 3600) -> str: ...

    def generate_download_url(self, key: str, *, expires_in: int = 3600) -> str: ...


class S3CompatStorage:
    """boto3 기반 S3 호환 스토리지. Cloudflare R2 / MinIO 양쪽에 동작."""

    def __init__(self, settings: Settings) -> None:
        self._bucket = settings.s3_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            config=Config(signature_version="s3v4"),
        )

    def build_resume_key(self, org_id: uuid.UUID, resume_id: uuid.UUID) -> str:
        return f"org_{org_id}/resume_{resume_id}.pdf"

    def generate_upload_url(self, key: str, *, expires_in: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def generate_download_url(self, key: str, *, expires_in: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
