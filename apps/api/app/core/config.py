"""Application settings loaded from environment via pydantic-settings."""

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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Lazy, cached settings accessor. Use this everywhere instead of importing
    a module-level `settings` instance, so tests can override via env vars and
    Alembic can lazy-load without side effects at import time."""
    return Settings()
