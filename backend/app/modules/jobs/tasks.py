import uuid
from typing import Any

import structlog
from redis.asyncio import Redis

from app.core.database import SessionLocal
from app.core.events import EVENTS_JOBS, publish
from app.modules.jobs import service as jobs_service
from app.modules.jobs.events import JobStatusEvent
from app.modules.jobs.schemas import JobStatus

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
            raw_text = await jobs_service.begin_extraction(session, job_uuid)
            await session.commit()
        await _emit(ctx, job_uuid, JobStatus.extracting)

        extraction, usage = await jobs_service.run_job_extraction(raw_text)

        async with SessionLocal() as session:
            await jobs_service.persist_job_extraction(session, job_uuid, extraction)
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
        await jobs_service.mark_job_failed(job_uuid, str(exc))
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
            url = await jobs_service.begin_scrape(session, job_uuid)
            await session.commit()
        await _emit(ctx, job_uuid, JobStatus.scraping)

        raw_text = await jobs_service.scrape_job(url)

        async with SessionLocal() as session:
            await jobs_service.persist_scraped_text(session, job_uuid, raw_text)
            await session.commit()
        await _emit(ctx, job_uuid, JobStatus.extracting)

        extraction, usage = await jobs_service.run_job_extraction(raw_text)

        async with SessionLocal() as session:
            await jobs_service.persist_job_extraction(session, job_uuid, extraction)
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
        await jobs_service.mark_job_failed(job_uuid, str(exc))
        await _emit(ctx, job_uuid, JobStatus.failed, str(exc))
        raise
