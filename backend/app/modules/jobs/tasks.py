import uuid
from typing import Any

import structlog
from redis.asyncio import Redis

from app.core.database import SessionLocal
from app.core.events import EVENTS_JOBS, publish
from app.modules.jobs import repository
from app.modules.jobs.events import JobStatusEvent
from app.modules.jobs.schemas import JobStatus
from app.modules.jobs.scraper import scrape_job_posting
from app.modules.jobs.service import (
    mark_job_failed,
    persist_job_extraction,
    run_job_extraction,
)

logger = structlog.get_logger(__name__)


async def _emit(
    ctx: dict[str, Any],
    job_id: uuid.UUID,
    status: JobStatus,
    error_message: str | None = None,
) -> None:
    """Publish a JobStatusEvent if the worker has a redis client attached."""
    redis = ctx.get("redis")
    if isinstance(redis, Redis):
        await publish(
            redis,
            EVENTS_JOBS,
            JobStatusEvent(job_id=job_id, status=status, error_message=error_message),
        )


async def extract_job(ctx: dict[str, Any], job_id: str) -> dict[str, Any]:
    """ARQ task: extract structured fields from a job's raw_text and embed.

    Three phases:
      1. Mark status='extracting' in its own transaction so polling clients
         see progress before the LLM call returns.
      2. Run the agent (no DB).
      3. Persist the extraction + status='ready' in one transaction so the
         user never sees a half-updated job.

    On any exception, mark the job failed (separate session, so the failure
    state survives the failing transaction's rollback) and re-raise so ARQ
    records the failure and retries up to max_tries.
    """
    job_uuid = uuid.UUID(job_id)
    logger.info("extract_job_start", job_id=job_id, job_try=ctx.get("job_try"))

    try:
        async with SessionLocal() as session:
            job = await repository.get_job(session, job_uuid)
            if job is None:
                raise RuntimeError(f"Job {job_uuid} not found")
            job.status = JobStatus.extracting
            job.error_message = None
            raw_text = job.raw_text
            await session.commit()
        await _emit(ctx, job_uuid, JobStatus.extracting)

        extraction, usage = await run_job_extraction(raw_text)

        async with SessionLocal() as session:
            await persist_job_extraction(session, job_uuid, extraction)
            job = await repository.get_job(session, job_uuid)
            if job is not None:
                job.status = JobStatus.ready
            await session.commit()
        await _emit(ctx, job_uuid, JobStatus.ready)

        logger.info(
            "extract_job_done",
            job_id=job_id,
            requirements=len(extraction.requirements),
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
        )
        return {
            "job_id": job_id,
            "status": "ready",
            "requirements": len(extraction.requirements),
        }
    except Exception as exc:
        logger.exception("extract_job_failed", job_id=job_id)
        await mark_job_failed(job_uuid, str(exc))
        await _emit(ctx, job_uuid, JobStatus.failed, str(exc))
        raise


async def scrape_and_extract_job(ctx: dict[str, Any], job_id: str) -> dict[str, Any]:
    """ARQ task: scrape a URL-source job, then extract structured fields.

    Phases (each committed in its own short transaction so polling clients
    see progress between long-running steps):
      1. status='scraping', clear error_message.
      2. Headless Chromium scrape (no DB).
      3. Persist scraped raw_text, status='extracting'.
      4. Run agent (no DB).
      5. Persist extraction + status='ready' (atomic).
    """
    job_uuid = uuid.UUID(job_id)
    logger.info("scrape_and_extract_job_start", job_id=job_id, job_try=ctx.get("job_try"))

    try:
        async with SessionLocal() as session:
            job = await repository.get_job(session, job_uuid)
            if job is None:
                raise RuntimeError(f"Job {job_uuid} not found")
            if not job.source_url:
                raise RuntimeError(f"Job {job_uuid} has no source_url")
            url = job.source_url
            job.status = JobStatus.scraping
            job.error_message = None
            await session.commit()
        await _emit(ctx, job_uuid, JobStatus.scraping)

        raw_text = await scrape_job_posting(url)

        async with SessionLocal() as session:
            job = await repository.get_job(session, job_uuid)
            if job is None:
                raise RuntimeError(f"Job {job_uuid} not found after scrape")
            job.raw_text = raw_text
            job.status = JobStatus.extracting
            await session.commit()
        await _emit(ctx, job_uuid, JobStatus.extracting)

        extraction, usage = await run_job_extraction(raw_text)

        async with SessionLocal() as session:
            await persist_job_extraction(session, job_uuid, extraction)
            job = await repository.get_job(session, job_uuid)
            if job is not None:
                job.status = JobStatus.ready
            await session.commit()
        await _emit(ctx, job_uuid, JobStatus.ready)

        logger.info(
            "scrape_and_extract_job_done",
            job_id=job_id,
            scraped_chars=len(raw_text),
            requirements=len(extraction.requirements),
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
        )
        return {
            "job_id": job_id,
            "status": "ready",
            "scraped_chars": len(raw_text),
            "requirements": len(extraction.requirements),
        }
    except Exception as exc:
        logger.exception("scrape_and_extract_job_failed", job_id=job_id)
        await mark_job_failed(job_uuid, str(exc))
        await _emit(ctx, job_uuid, JobStatus.failed, str(exc))
        raise
