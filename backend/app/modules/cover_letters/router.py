import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.database import SessionLocal
from app.core.http import conflict_on
from app.core.security import AuthUser, get_current_user
from app.modules.cover_letters import service
from app.modules.cover_letters.schemas import CoverLetterDraftRead
from app.modules.shared.feature_context import FeaturePrerequisitesError, NoMatchRunError

router = APIRouter(prefix="/cover-letters", tags=["cover_letters"])


@router.post(
    "/{job_id}/generate",
    response_model=CoverLetterDraftRead,
    operation_id="generate_cover_letter",
)
async def generate_cover_letter_for_job(
    job_id: uuid.UUID,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> CoverLetterDraftRead:
    """Draft a cover letter using the latest match run + CV chunks."""
    async with SessionLocal() as session:
        with conflict_on(NoMatchRunError, FeaturePrerequisitesError):
            draft = await service.generate_cover_letter(session, current_user.id, job_id)

        await session.commit()
        return CoverLetterDraftRead.model_validate(draft)


@router.get("/{job_id}", response_model=list[CoverLetterDraftRead])
async def get_cover_letters(
    job_id: uuid.UUID,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> list[CoverLetterDraftRead]:
    async with SessionLocal() as session:
        drafts = await service.list_for_job(session, current_user.id, job_id)
        return [CoverLetterDraftRead.model_validate(d) for d in drafts]
