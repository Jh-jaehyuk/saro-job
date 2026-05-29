"""Resume 라우터 — 업로드 URL 발급 + finalize."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_org_id
from app.core.db import get_session
from app.schemas.resume import (
    ResumeFinalizeRequest,
    ResumeProcessingJobRead,
    ResumeUploadRequest,
    ResumeUploadResponse,
)
from app.services import resume_service
from app.services.storage import ObjectStorage, get_storage

router = APIRouter(prefix="/resumes", tags=["resumes"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
OrgDep = Annotated[uuid.UUID, Depends(current_org_id)]
StorageDep = Annotated[ObjectStorage, Depends(get_storage)]


@router.post("/upload-url")
async def create_upload_url(
    _: ResumeUploadRequest,
    session: SessionDep,
    org_id: OrgDep,
    storage: StorageDep,
) -> ResumeUploadResponse:
    resume, upload_url = await resume_service.create_resume_with_upload_url(
        session, storage, org_id
    )
    return ResumeUploadResponse(resume_id=resume.id, upload_url=upload_url)


@router.post("/{resume_id}/finalize", status_code=status.HTTP_202_ACCEPTED)
async def finalize_resume(
    resume_id: uuid.UUID,
    data: ResumeFinalizeRequest,
    session: SessionDep,
    org_id: OrgDep,
) -> ResumeProcessingJobRead:
    job = await resume_service.finalize_resume(session, org_id, resume_id, data.jd_id)
    return ResumeProcessingJobRead.model_validate(job)
