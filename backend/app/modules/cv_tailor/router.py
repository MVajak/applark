import uuid

from fastapi import APIRouter

from app.core.database import SessionLocal
from app.core.http import conflict_on
from app.modules.cv_tailor import repository, service
from app.modules.cv_tailor.schemas import CVTailorRunRead
from app.modules.shared.feature_context import FeaturePrerequisitesError, NoMatchRunError

router = APIRouter(prefix="/cv-tailor", tags=["cv_tailor"])


@router.post("/{job_id}/run", response_model=CVTailorRunRead)
async def run_cv_tailor(job_id: uuid.UUID) -> CVTailorRunRead:
    """Run the tailor agent synchronously (~5-10s for one Sonnet call)."""
    async with SessionLocal() as session:
        with conflict_on(NoMatchRunError, FeaturePrerequisitesError):
            run = await service.run_cv_tailor(session, job_id)

        await session.commit()
        return CVTailorRunRead.model_validate(run)


@router.get("/{job_id}/latest", response_model=CVTailorRunRead | None)
async def get_latest_cv_tailor(job_id: uuid.UUID) -> CVTailorRunRead | None:
    async with SessionLocal() as session:
        run = await repository.get_latest_for_job(session, job_id)
        if run is None:
            return None
        return CVTailorRunRead.model_validate(run)
