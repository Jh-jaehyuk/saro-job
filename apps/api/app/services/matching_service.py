"""Match 읽기 서비스. 테넌트 격리는 JobDescription.org_id 조인으로 강제.

스코어링(점수 계산) 로직은 파이프라인 PR에서 추가한다 — 여기서는 조회만.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import JobDescriptionNotFound, MatchNotFound
from app.models.interview_question import InterviewQuestion
from app.models.job_description import JobDescription
from app.models.match import Match


async def list_matches_for_jd(
    session: AsyncSession, org_id: uuid.UUID, jd_id: uuid.UUID
) -> list[Match]:
    jd = (
        await session.execute(
            select(JobDescription.id).where(
                JobDescription.id == jd_id, JobDescription.org_id == org_id
            )
        )
    ).scalar_one_or_none()
    if jd is None:
        raise JobDescriptionNotFound()

    result = await session.execute(
        select(Match).where(Match.jd_id == jd_id).order_by(Match.overall_score.desc())
    )
    return list(result.scalars().all())


async def get_match(session: AsyncSession, org_id: uuid.UUID, match_id: uuid.UUID) -> Match:
    result = await session.execute(
        select(Match)
        .join(JobDescription, Match.jd_id == JobDescription.id)
        .where(Match.id == match_id, JobDescription.org_id == org_id)
    )
    match = result.scalar_one_or_none()
    if match is None:
        raise MatchNotFound()
    return match


async def list_questions(
    session: AsyncSession, org_id: uuid.UUID, match_id: uuid.UUID
) -> list[InterviewQuestion]:
    # org 소유 검증(없으면 MatchNotFound).
    await get_match(session, org_id, match_id)
    result = await session.execute(
        select(InterviewQuestion)
        .where(InterviewQuestion.match_id == match_id)
        .order_by(InterviewQuestion.order)
    )
    return list(result.scalars().all())
