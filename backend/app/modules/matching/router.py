import uuid

from fastapi import APIRouter

from app.core.database import SessionLocal
from app.core.http import conflict_on, not_found_on
from app.modules.matching import service as matching_service
from app.modules.matching.schemas import MatchRunRead
from app.modules.matching.service import (
    JobNotFoundError,
    JobNotReadyError,
    MissingEmbeddingsError,
    NoCVUploadedError,
    run_match,
)

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post(
    "/{job_id}/run",
    response_model=MatchRunRead,
    operation_id="run_match",
)
async def run_match_for_job(job_id: uuid.UUID) -> MatchRunRead:
    """Run the matcher synchronously (~5-10s for one Sonnet call)."""
    async with SessionLocal() as session:
        with (
            not_found_on(JobNotFoundError),
            conflict_on(JobNotReadyError, NoCVUploadedError, MissingEmbeddingsError),
        ):
            run = await run_match(session, job_id)

        await session.commit()
        return MatchRunRead.model_validate(run)


@router.get("/{job_id}/latest", response_model=MatchRunRead | None)
async def get_latest_match(job_id: uuid.UUID) -> MatchRunRead | None:
    async with SessionLocal() as session:
        run = await matching_service.get_latest_for_job(session, job_id)
        if run is None:
            return None
        return MatchRunRead.model_validate(run)


@router.get("/{job_id}/history", response_model=list[MatchRunRead])
async def get_match_history(job_id: uuid.UUID) -> list[MatchRunRead]:
    async with SessionLocal() as session:
        runs = await matching_service.get_history_for_job(session, job_id)
        return [MatchRunRead.model_validate(r) for r in runs]
