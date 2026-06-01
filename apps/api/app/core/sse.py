"""진행률 발행 경계.

파이프라인이 단계 완료마다 진행률을 발행한다. 실제 Redis pub/sub 구현과
`/jds/{id}/progress` SSE 엔드포인트는 SSE PR에서 추가한다 — 여기서는 인터페이스와
no-op 기본 구현만 둔다.
"""

import uuid
from typing import Protocol


class ProgressPublisher(Protocol):
    async def publish(
        self, jd_id: uuid.UUID, *, resume_id: uuid.UUID, step: str, percent: int
    ) -> None: ...


class NoopProgressPublisher:
    """아무것도 발행하지 않는 기본 구현. Redis 발행은 SSE PR."""

    async def publish(
        self, jd_id: uuid.UUID, *, resume_id: uuid.UUID, step: str, percent: int
    ) -> None:
        return None
