import uuid
from typing import Annotated

from arq import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from redis.asyncio import Redis

from app.core.database import SessionLocal
from app.core.events import EVENTS_JOBS, publish, sse_response
from app.core.redis import get_arq_pool, get_redis
from app.modules.jobs import repository
from app.modules.jobs.events import JobStatusEvent
from app.modules.jobs.models import Job
from app.modules.jobs.schemas import (
    CreateJobFromText,
    CreateJobFromUrl,
    JobListItem,
    JobRead,
    JobSourceKind,
    JobStatus,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "/from-text",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobRead,
)
async def create_job_from_text(
    payload: CreateJobFromText,
    arq_pool: Annotated[ArqRedis, Depends(get_arq_pool)],
) -> JobRead:
    async with SessionLocal() as session:
        if payload.source_url is not None:
            existing = await repository.get_by_url(session, payload.source_url)
            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "message": f"Job already exists for source_url={payload.source_url}",
                        "existing_job_id": str(existing.id),
                    },
                )

        job = Job(
            source_kind=JobSourceKind.pasted,
            raw_text=payload.raw_text,
            source_url=payload.source_url,
            status=JobStatus.pending,
        )
        job = await repository.add_job(session, job)
        await session.commit()
        await session.refresh(job, attribute_names=["requirements"])
        response = JobRead.model_validate(job)

    await arq_pool.enqueue_job("extract_job", str(job.id))
    return response


@router.post(
    "/from-url",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobRead,
)
async def create_job_from_url(
    payload: CreateJobFromUrl,
    arq_pool: Annotated[ArqRedis, Depends(get_arq_pool)],
) -> JobRead:
    url = str(payload.source_url)

    async with SessionLocal() as session:
        existing = await repository.get_by_url(session, url)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": f"Job already exists for source_url={url}",
                    "existing_job_id": str(existing.id),
                },
            )

        job = Job(
            source_kind=JobSourceKind.url,
            source_url=url,
            raw_text="",
            status=JobStatus.pending,
        )
        job = await repository.add_job(session, job)
        await session.commit()
        await session.refresh(job, attribute_names=["requirements"])
        response = JobRead.model_validate(job)

    await arq_pool.enqueue_job("scrape_and_extract_job", str(job.id))
    return response


@router.get("", response_model=list[JobListItem])
async def get_jobs(
    status_filter: Annotated[JobStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[JobListItem]:
    async with SessionLocal() as session:
        jobs = await repository.list_jobs(session, status=status_filter, limit=limit, offset=offset)
        return [JobListItem.model_validate(j) for j in jobs]


# Declared before `/{job_id}` so FastAPI's in-order matcher doesn't treat
# "events" as a UUID path param.
@router.get("/events", include_in_schema=False)
async def job_events(
    request: Request,
    redis: Annotated[Redis, Depends(get_redis)],
) -> StreamingResponse:
    """SSE stream of JobStatusEvent JSON frames.

    Excluded from the OpenAPI schema so orval doesn't generate a fetch hook
    for an endpoint that returns text/event-stream.
    """
    return sse_response(request, redis, EVENTS_JOBS)


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: uuid.UUID) -> JobRead:
    async with SessionLocal() as session:
        job = await repository.get_job_with_requirements(session, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobRead.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: uuid.UUID) -> None:
    async with SessionLocal() as session:
        deleted = await repository.delete_job(session, job_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Job not found")
        await session.commit()


@router.post(
    "/{job_id}/retry",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobRead,
)
async def retry_job(
    job_id: uuid.UUID,
    arq_pool: Annotated[ArqRedis, Depends(get_arq_pool)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> JobRead:
    async with SessionLocal() as session:
        job = await repository.get_job_with_requirements(session, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.status != JobStatus.failed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(f"Job status is '{job.status.value}'; only 'failed' jobs can be retried"),
            )

        task_name = (
            "scrape_and_extract_job" if job.source_kind == JobSourceKind.url else "extract_job"
        )

        job.status = JobStatus.pending
        job.error_message = None
        await session.commit()
        # updated_at is server-set via onupdate=func.now(), so SQLA expires
        # it after commit — refresh it explicitly along with requirements.
        await session.refresh(job, attribute_names=["updated_at", "requirements"])
        response = JobRead.model_validate(job)

    await publish(redis, EVENTS_JOBS, JobStatusEvent(job_id=job_id, status=JobStatus.pending))
    await arq_pool.enqueue_job(task_name, str(job_id))
    return response
