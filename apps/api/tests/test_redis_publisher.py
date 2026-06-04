"""RedisProgressPublisher pub/sub 통합 테스트(실 redis 사용).

CI는 redis service container로, 로컬은 `docker compose --profile integration up redis`.
"""

import asyncio
import json
import uuid

import pytest
import redis.asyncio as aioredis
from app.core.config import get_settings
from app.core.sse import RedisProgressPublisher, progress_channel


@pytest.mark.asyncio
async def test_publish_delivers_to_subscriber() -> None:
    client = aioredis.from_url(get_settings().redis_url)
    jd_id = uuid.uuid4()
    resume_id = uuid.uuid4()

    pubsub = client.pubsub()
    await pubsub.subscribe(progress_channel(jd_id))

    publisher = RedisProgressPublisher(client)
    # 구독 셋업이 redis에 닿을 시간 확보.
    await asyncio.sleep(0.05)
    await publisher.publish(jd_id, resume_id=resume_id, step="parsed", percent=20)

    # 첫 메시지(구독 확인은 ignore)는 publish 데이터.
    received = None
    for _ in range(20):
        msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.1)
        if msg is not None:
            received = msg
            break

    assert received is not None
    payload = json.loads(received["data"])
    assert payload == {"resume_id": str(resume_id), "step": "parsed", "percent": 20}

    await pubsub.unsubscribe(progress_channel(jd_id))
    await pubsub.aclose()
    await client.aclose()
