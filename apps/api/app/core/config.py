"""Application settings loaded from environment via pydantic-settings."""

from decimal import Decimal
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. All values read from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sarojob"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Object storage (S3-compatible)
    s3_endpoint_url: str = "http://localhost:9000"
    s3_region: str = "auto"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_bucket: str = "sarojob-local"

    # Runtime
    app_env: Literal["local", "dev", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # SSE
    # heartbeat 간격(초). 운영 30s, 테스트는 monkeypatch로 짧게 override.
    sse_heartbeat_seconds: float = 30.0

    # Auth
    auth_secret_key: str = "change-me-in-prod-this-is-a-development-only-default"
    auth_cookie_secure: bool = False
    auth_cookie_max_age: int = 60 * 60 * 24 * 7  # 7 days
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_url: str = "http://localhost:8000/auth/google/callback"

    # LLM (OpenAI). 키가 비어 있으면 워커는 placeholder 클라이언트로 동작한다.
    openai_api_key: str = ""
    # 단순 추출·분류 위주라 저렴한 모델이 기본값. 가격표(`services/llm.py`)에 있는 모델만 허용.
    llm_chat_model: str = "gpt-4o-mini"
    llm_embedding_model: str = "text-embedding-3-small"
    # 입력 상한(문자 수). 초과분은 잘라서 보낸다 — 긴 이력서 한 건이 비용을 폭증시키지 않게.
    llm_max_input_chars: int = 12_000
    # 출력 상한(토큰). 구조화 응답은 이 안에 충분히 들어간다.
    llm_max_output_tokens: int = 1_024
    # 조직별 하루(UTC) LLM 비용 한도(USD). 0이면 한도 없음.
    llm_daily_budget_usd_per_org: Decimal = Decimal("1.00")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Lazy, cached settings accessor. Use this everywhere instead of importing
    a module-level `settings` instance, so tests can override via env vars and
    Alembic can lazy-load without side effects at import time."""
    return Settings()
