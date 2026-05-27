import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.database import SessionLocal
from app.modules.jobs import repository as jobs_repository
from app.modules.jobs.schemas import JobStatus
from app.modules.matching import repository
from app.modules.matching.schemas import MatchRunRead
from app.modules.matching.service import (
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
        job = await jobs_repository.get_job(session, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.status != JobStatus.ready:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Job status is '{job.status.value}'; matching requires "
                    "'ready'. Wait for extraction to finish or retry the job."
                ),
            )

        try:
            run = await run_match(session, job_id)
        except NoCVUploadedError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(exc)
            ) from exc
        except MissingEmbeddingsError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(exc)
            ) from exc

        await session.commit()
        return MatchRunRead.model_validate(run)


@router.get("/{job_id}/latest", response_model=MatchRunRead | None)
async def get_latest_match(job_id: uuid.UUID) -> MatchRunRead | None:
    async with SessionLocal() as session:
        run = await repository.get_latest_for_job(session, job_id)
        if run is None:
            return None
        return MatchRunRead.model_validate(run)


@router.get("/{job_id}/history", response_model=list[MatchRunRead])
async def get_match_history(job_id: uuid.UUID) -> list[MatchRunRead]:
    async with SessionLocal() as session:
        runs = await repository.get_history_for_job(session, job_id)
        return [MatchRunRead.model_validate(r) for r in runs]
