import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.database import SessionLocal
from app.modules.interview_prep import repository, service
from app.modules.interview_prep.schemas import InterviewPrepRunRead

router = APIRouter(prefix="/interview-prep", tags=["interview_prep"])


@router.post("/{job_id}/generate", response_model=InterviewPrepRunRead)
async def generate_interview_prep(job_id: uuid.UUID) -> InterviewPrepRunRead:
    """Generate interview prep synchronously (~5-10s for one Sonnet call)."""
    async with SessionLocal() as session:
        try:
            run = await service.generate_interview_prep(session, job_id)
        except service.NoMatchRunError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(exc)
            ) from exc
        except service.InterviewPrepPrerequisitesError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(exc)
            ) from exc

        await session.commit()
        return InterviewPrepRunRead.model_validate(run)


@router.get("/{job_id}/latest", response_model=InterviewPrepRunRead | None)
async def get_latest_interview_prep(
    job_id: uuid.UUID,
) -> InterviewPrepRunRead | None:
    async with SessionLocal() as session:
        run = await repository.get_latest_for_job(session, job_id)
        if run is None:
            return None
        return InterviewPrepRunRead.model_validate(run)
