"""JobDescription 도메인 서비스. org_id로 테넌트 격리(AGENTS §8).

세션은 인자로 받고 `commit()`하지 않는다(AGENTS §7) — 라우터의 get_session이 관리.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import JobDescriptionNotFound
from app.models.job_description import JobDescription
from app.models.resume_processing_job import ResumeProcessingJob
from app.schemas.job_description import JobDescriptionCreate


async def create_jd(
    session: AsyncSession, org_id: uuid.UUID, data: JobDescriptionCreate
) -> JobDescription:
    jd = JobDescription(
        org_id=org_id,
        title=data.title,
        raw_text=data.raw_text,
        requirements_json={},
    )
    session.add(jd)
    await session.flush()
    return jd


async def list_jds(session: AsyncSession, org_id: uuid.UUID) -> list[JobDescription]:
    result = await session.execute(
        select(JobDescription)
        .where(JobDescription.org_id == org_id)
        .order_by(JobDescription.created_at.desc())
    )
    return list(result.scalars().all())


async def get_jd(session: AsyncSession, org_id: uuid.UUID, jd_id: uuid.UUID) -> JobDescription:
    result = await session.execute(
        select(JobDescription).where(JobDescription.id == jd_id, JobDescription.org_id == org_id)
    )
    jd = result.scalar_one_or_none()
    if jd is None:
        raise JobDescriptionNotFound()
    return jd


async def list_processing_jobs(
    session: AsyncSession, org_id: uuid.UUID, jd_id: uuid.UUID
) -> list[ResumeProcessingJob]:
    """JD 소유 검증 후 해당 JD의 모든 처리 잡 row를 반환(SSE 재연결 동기화용)."""
    await get_jd(session, org_id, jd_id)
    result = await session.execute(
        select(ResumeProcessingJob)
        .where(ResumeProcessingJob.jd_id == jd_id)
        .order_by(ResumeProcessingJob.created_at.desc())
    )
    return list(result.scalars().all())
