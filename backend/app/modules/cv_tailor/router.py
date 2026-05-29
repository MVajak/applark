import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.database import SessionLocal
from app.core.http import conflict_on
from app.core.security import AuthUser, get_current_user
from app.modules.cv_tailor import service
from app.modules.cv_tailor.schemas import CVTailorRunRead
from app.modules.shared.feature_context import FeaturePrerequisitesError, NoMatchRunError

router = APIRouter(prefix="/cv-tailor", tags=["cv_tailor"])


@router.post("/{job_id}/run", response_model=CVTailorRunRead)
async def run_cv_tailor(
    job_id: uuid.UUID,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> CVTailorRunRead:
    """Run the tailor agent synchronously (~5-10s for one Sonnet call)."""
    async with SessionLocal() as session:
        with conflict_on(NoMatchRunError, FeaturePrerequisitesError):
            run = await service.run_cv_tailor(session, current_user.id, job_id)

        await session.commit()
        return CVTailorRunRead.model_validate(run)


@router.get("/{job_id}/latest", response_model=CVTailorRunRead | None)
async def get_latest_cv_tailor(
    job_id: uuid.UUID,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> CVTailorRunRead | None:
    async with SessionLocal() as session:
        run = await service.get_latest_for_job(session, current_user.id, job_id)
        if run is None:
            return None
        return CVTailorRunRead.model_validate(run)
