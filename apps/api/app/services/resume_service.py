"""Resume 도메인 서비스. 업로드 URL 발급 + finalize(처리 잡 생성 + ARQ enqueue).

브라우저가 presigned PUT으로 R2에 직접 올린다(ARCHITECTURE §6.1). 백엔드는 결정적
키로 Resume row를 먼저 만들고 URL만 발급한다. finalize는 잡 row를 만들고 ARQ 큐에
`process_resume`를 적재한다.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import JobDescriptionNotFound, ResumeNotFound
from app.core.queue import QUEUE_NAME
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.models.resume_processing_job import ResumeProcessingJob
from app.services import llm_budget
from app.services.storage import ObjectStorage


async def create_resume_with_upload_url(
    session: AsyncSession, storage: ObjectStorage, org_id: uuid.UUID
) -> tuple[Resume, str]:
    resume_id = uuid.uuid4()
    key = storage.build_resume_key(org_id, resume_id)
    resume = Resume(id=resume_id, org_id=org_id, pdf_key=key)
    session.add(resume)
    await session.flush()
    upload_url = storage.generate_upload_url(key)
    return resume, upload_url


async def finalize_resume(
    session: AsyncSession,
    arq_pool: Any,
    org_id: uuid.UUID,
    resume_id: uuid.UUID,
    jd_id: uuid.UUID,
) -> ResumeProcessingJob:
    # resume·jd 모두 호출자 org 소유인지 검증(아니면 404로 존재 은닉).
    resume = (
        await session.execute(select(Resume).where(Resume.id == resume_id, Resume.org_id == org_id))
    ).scalar_one_or_none()
    if resume is None:
        raise ResumeNotFound()

    jd = (
        await session.execute(
            select(JobDescription).where(
                JobDescription.id == jd_id, JobDescription.org_id == org_id
            )
        )
    ).scalar_one_or_none()
    if jd is None:
        raise JobDescriptionNotFound()

    # 멱등: 같은 (resume, jd) 잡이 이미 있으면 그대로 반환.
    existing = (
        await session.execute(
            select(ResumeProcessingJob).where(
                ResumeProcessingJob.resume_id == resume_id,
                ResumeProcessingJob.jd_id == jd_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    # 오늘 한도를 이미 다 쓴 조직은 큐에 넣기 전에 거절(429) — 워커에서 실패시키는 것보다
    # 사용자가 즉시 이유를 알 수 있다.
    await llm_budget.ensure_within_budget(
        session, org_id, get_settings().llm_daily_budget_usd_per_org
    )

    job = ResumeProcessingJob(resume_id=resume_id, jd_id=jd_id, state="queued", step_state_json={})
    session.add(job)
    await session.flush()
    # 새 잡일 때만 큐에 적재 — 같은 (resume, jd) 재호출은 위 멱등 분기에서 잡혀
    # 여기까지 안 온다. 워커는 LLM placeholder 한도 내에서 parsed 단계까지 처리한다.
    await arq_pool.enqueue_job("process_resume", str(resume_id), str(jd_id), _queue_name=QUEUE_NAME)
    return job
