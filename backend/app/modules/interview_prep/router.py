import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.database import SessionLocal
from app.core.http import conflict_on
from app.core.security import AuthUser, get_current_user
from app.modules.interview_prep import service
from app.modules.interview_prep.schemas import InterviewPrepRunRead
from app.modules.shared.feature_context import FeaturePrerequisitesError, NoMatchRunError

router = APIRouter(prefix="/interview-prep", tags=["interview_prep"])


@router.post("/{job_id}/generate", response_model=InterviewPrepRunRead)
async def generate_interview_prep(
    job_id: uuid.UUID,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> InterviewPrepRunRead:
    """Generate interview prep synchronously (~5-10s for one Sonnet call)."""
    async with SessionLocal() as session:
        with conflict_on(NoMatchRunError, FeaturePrerequisitesError):
            run = await service.generate_interview_prep(session, current_user.id, job_id)

        await session.commit()
        return InterviewPrepRunRead.model_validate(run)


@router.get("/{job_id}/latest", response_model=InterviewPrepRunRead | None)
async def get_latest_interview_prep(
    job_id: uuid.UUID,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> InterviewPrepRunRead | None:
    async with SessionLocal() as session:
        run = await service.get_latest_for_job(session, current_user.id, job_id)
        if run is None:
            return None
        return InterviewPrepRunRead.model_validate(run)
