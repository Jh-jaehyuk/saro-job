"""진행률 발행 경계 + Redis 구현.

파이프라인이 단계 완료마다 진행률을 발행한다(ARCHITECTURE §6.2/§6.3).
`RedisProgressPublisher`가 채널 `jd:{jd_id}:progress`에 JSON을 발행하면 API SSE
엔드포인트가 구독하여 EventSource 클라이언트로 전달한다.
"""

import json
import uuid
from typing import Protocol

import redis.asyncio as aioredis


def progress_channel(jd_id: uuid.UUID) -> str:
    return f"jd:{jd_id}:progress"


class ProgressPublisher(Protocol):
    async def publish(
        self, jd_id: uuid.UUID, *, resume_id: uuid.UUID, step: str, percent: int
    ) -> None: ...


class NoopProgressPublisher:
    """아무것도 발행하지 않는 기본 구현. 테스트/유닛 격리용."""

    async def publish(
        self, jd_id: uuid.UUID, *, resume_id: uuid.UUID, step: str, percent: int
    ) -> None:
        return None


class RedisProgressPublisher:
    """Redis pub/sub로 진행률을 발행. SSE 엔드포인트가 같은 채널을 구독한다."""

    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def publish(
        self, jd_id: uuid.UUID, *, resume_id: uuid.UUID, step: str, percent: int
    ) -> None:
        payload = json.dumps({"resume_id": str(resume_id), "step": step, "percent": percent})
        await self._redis.publish(progress_channel(jd_id), payload)
