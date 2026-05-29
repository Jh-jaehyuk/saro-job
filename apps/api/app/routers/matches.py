"""Match 조회 라우터. 경로가 /jds와 /matches에 걸쳐 있어 prefix 없이 전체 경로 명시."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_org_id
from app.core.db import get_session
from app.schemas.match import InterviewQuestionRead, MatchRead
from app.services import matching_service

router = APIRouter(tags=["matches"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
OrgDep = Annotated[uuid.UUID, Depends(current_org_id)]


@router.get("/jds/{jd_id}/matches")
async def list_matches_for_jd(
    jd_id: uuid.UUID, session: SessionDep, org_id: OrgDep
) -> list[MatchRead]:
    matches = await matching_service.list_matches_for_jd(session, org_id, jd_id)
    return [MatchRead.model_validate(m) for m in matches]


@router.get("/matches/{match_id}")
async def get_match(match_id: uuid.UUID, session: SessionDep, org_id: OrgDep) -> MatchRead:
    match = await matching_service.get_match(session, org_id, match_id)
    return MatchRead.model_validate(match)


@router.get("/matches/{match_id}/questions")
async def list_match_questions(
    match_id: uuid.UUID, session: SessionDep, org_id: OrgDep
) -> list[InterviewQuestionRead]:
    questions = await matching_service.list_questions(session, org_id, match_id)
    return [InterviewQuestionRead.model_validate(q) for q in questions]
