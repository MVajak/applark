import uuid

from fastapi import APIRouter

from app.core.database import SessionLocal
from app.core.http import conflict_on
from app.modules.interview_prep import service
from app.modules.interview_prep.schemas import InterviewPrepRunRead
from app.modules.shared.feature_context import FeaturePrerequisitesError, NoMatchRunError

router = APIRouter(prefix="/interview-prep", tags=["interview_prep"])


@router.post("/{job_id}/generate", response_model=InterviewPrepRunRead)
async def generate_interview_prep(job_id: uuid.UUID) -> InterviewPrepRunRead:
    """Generate interview prep synchronously (~5-10s for one Sonnet call)."""
    async with SessionLocal() as session:
        with conflict_on(NoMatchRunError, FeaturePrerequisitesError):
            run = await service.generate_interview_prep(session, job_id)

        await session.commit()
        return InterviewPrepRunRead.model_validate(run)


@router.get("/{job_id}/latest", response_model=InterviewPrepRunRead | None)
async def get_latest_interview_prep(
    job_id: uuid.UUID,
) -> InterviewPrepRunRead | None:
    async with SessionLocal() as session:
        run = await service.get_latest_for_job(session, job_id)
        if run is None:
            return None
        return InterviewPrepRunRead.model_validate(run)
