"""Resume 도메인 서비스. 업로드 URL 발급 + finalize(처리 잡 생성).

브라우저가 presigned PUT으로 R2에 직접 올린다(ARCHITECTURE §6.1). 백엔드는 결정적
키로 Resume row를 먼저 만들고 URL만 발급한다.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import JobDescriptionNotFound, ResumeNotFound
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.models.resume_processing_job import ResumeProcessingJob
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

    job = ResumeProcessingJob(resume_id=resume_id, jd_id=jd_id, state="queued", step_state_json={})
    session.add(job)
    await session.flush()
    # TODO(파이프라인 PR): 여기서 ARQ `process_resume(resume_id, jd_id)`를 enqueue.
    #   현재는 워커 핸들러가 없어 row만 'queued' 상태로 남긴다.
    return job
