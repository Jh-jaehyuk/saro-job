"""Redis 클라이언트 의존성.

`get_redis()`가 lazy 모듈 캐시로 단일 `redis.asyncio.Redis` 인스턴스를 만들어
공유한다. SSE pub/sub은 별도로 매 연결마다 `client.pubsub()`을 생성하므로 공유
클라이언트로 충분하다(#8 `core/queue.py:get_arq_pool` 패턴과 동일).
"""

from __future__ import annotations

import redis.asyncio as aioredis

from app.core.config import get_settings

_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(get_settings().redis_url)  # type: ignore[no-untyped-call]
    return _client


async def close_redis() -> None:
    """앱 종료 정리(lifespan 도입 시 호출)."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
