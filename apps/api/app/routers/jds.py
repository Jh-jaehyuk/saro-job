"""JD 라우터 — 얇은 HTTP 어댑터. 인증·테넌트는 current_active_user로 강제."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_org_id
from app.core.db import get_session
from app.schemas.job_description import JobDescriptionCreate, JobDescriptionRead
from app.services import jd_service

router = APIRouter(prefix="/jds", tags=["jds"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
OrgDep = Annotated[uuid.UUID, Depends(current_org_id)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_jd(
    data: JobDescriptionCreate, session: SessionDep, org_id: OrgDep
) -> JobDescriptionRead:
    jd = await jd_service.create_jd(session, org_id, data)
    return JobDescriptionRead.model_validate(jd)


@router.get("")
async def list_jds(session: SessionDep, org_id: OrgDep) -> list[JobDescriptionRead]:
    jds = await jd_service.list_jds(session, org_id)
    return [JobDescriptionRead.model_validate(jd) for jd in jds]


@router.get("/{jd_id}")
async def get_jd(jd_id: uuid.UUID, session: SessionDep, org_id: OrgDep) -> JobDescriptionRead:
    jd = await jd_service.get_jd(session, org_id, jd_id)
    return JobDescriptionRead.model_validate(jd)
