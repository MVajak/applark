import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.database import SessionLocal
from app.modules.cv_tailor import repository, service
from app.modules.cv_tailor.schemas import CVTailorRunRead

router = APIRouter(prefix="/cv-tailor", tags=["cv_tailor"])


@router.post("/{job_id}/run", response_model=CVTailorRunRead)
async def run_cv_tailor(job_id: uuid.UUID) -> CVTailorRunRead:
    """Run the tailor agent synchronously (~5-10s for one Sonnet call)."""
    async with SessionLocal() as session:
        try:
            run = await service.run_cv_tailor(session, job_id)
        except service.NoMatchRunError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(exc)
            ) from exc
        except service.CVTailorPrerequisitesError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(exc)
            ) from exc

        await session.commit()
        return CVTailorRunRead.model_validate(run)


@router.get("/{job_id}/latest", response_model=CVTailorRunRead | None)
async def get_latest_cv_tailor(job_id: uuid.UUID) -> CVTailorRunRead | None:
    async with SessionLocal() as session:
        run = await repository.get_latest_for_job(session, job_id)
        if run is None:
            return None
        return CVTailorRunRead.model_validate(run)
