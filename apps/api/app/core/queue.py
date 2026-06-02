"""ARQ Redis 풀 의존성.

FastAPI 라우터가 `Depends(get_arq_pool)`로 풀을 받아 `enqueue_job`을 호출한다.
풀은 첫 호출 시 lazy하게 만들고 이후 모듈 캐시로 재사용한다 — lifespan에서 만들면
테스트 진입 시점에 redis가 없어 깨지기 때문(라우터 테스트는 의존성 override).
"""

from __future__ import annotations

from typing import Any

from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import get_settings

QUEUE_NAME = "saro-job:default"

_pool: Any = None


async def get_arq_pool() -> Any:
    """ARQ Redis 풀(`ArqRedis`)을 lazy하게 만들어 캐시 반환."""
    global _pool
    if _pool is None:
        _pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    return _pool


async def close_arq_pool() -> None:
    """앱 종료 정리(lifespan 도입 시 호출)."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
