"""SSE 진행률 구독 + 재연결 동기화용 상태 조회 라우터.

EventSource는 커스텀 헤더를 못 보내므로 인증은 fastapi-users 쿠키 흐름으로 처리한다
(ARCHITECTURE §6.3). 채널은 `jd:{jd_id}:progress`. 워커가 발행, 이 라우터가 구독.
"""

import asyncio
import uuid
from collections.abc import AsyncIterator
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_org_id
from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.core.redis import get_redis
from app.core.sse import progress_channel
from app.schemas.resume import ResumeProcessingJobRead
from app.services import jd_service

router = APIRouter(tags=["progress"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
OrgDep = Annotated[uuid.UUID, Depends(current_org_id)]
RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/jds/{jd_id}/status")
async def get_progress_status(
    jd_id: uuid.UUID, session: SessionDep, org_id: OrgDep
) -> list[ResumeProcessingJobRead]:
    jobs = await jd_service.list_processing_jobs(session, org_id, jd_id)
    return [ResumeProcessingJobRead.model_validate(j) for j in jobs]


@router.get("/jds/{jd_id}/progress")
async def stream_progress(
    jd_id: uuid.UUID,
    session: SessionDep,
    org_id: OrgDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> StreamingResponse:
    # JD 소유 검증(없으면 JobDescriptionNotFound 404).
    await jd_service.get_jd(session, org_id, jd_id)

    channel = progress_channel(jd_id)
    heartbeat = settings.sse_heartbeat_seconds

    async def event_stream() -> AsyncIterator[bytes]:
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)
        try:
            while True:
                try:
                    msg = await pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=heartbeat
                    )
                except asyncio.CancelledError:
                    break
                if msg is None:
                    yield b": heartbeat\n\n"
                    continue
                data = msg["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                yield f"data: {data}\n\n".encode()
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()  # type: ignore[no-untyped-call]

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
