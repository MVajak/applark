import uuid
from collections.abc import Sequence

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import providers
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.embeddings import get_embedding, get_embeddings
from app.core.llm import extract_token_usage
from app.modules.billing.protocols import BillingProvider
from app.modules.jobs import repository
from app.modules.jobs.agent import job_extractor
from app.modules.jobs.models import Job, JobRequirement
from app.modules.jobs.schemas import (
    CreateJobFromText,
    CreateJobFromUrl,
    JobExtraction,
    JobSourceKind,
    JobStatus,
)
from app.modules.jobs.scraper import scrape_job_posting

logger = structlog.get_logger(__name__)


class DuplicateJobError(RuntimeError):
    """A job already exists for the given source_url."""

    def __init__(self, existing_id: uuid.UUID) -> None:
        super().__init__(f"Job already exists for that source_url (id={existing_id})")
        self.existing_id = existing_id


class JobNotRetriableError(RuntimeError):
    """Retry was requested for a job that isn't in the 'failed' state."""


# Hard cap so a pathologically long scrape (cookie banners, embedded
# transcripts, etc.) can't blow up our per-call Anthropic cost.
MAX_RAW_TEXT_CHARS = 20_000


async def run_job_extraction(
    raw_text: str,
) -> tuple[JobExtraction, dict[str, int | None]]:
    """Run the job extractor agent on raw text. Returns output + token usage."""
    if len(raw_text) > MAX_RAW_TEXT_CHARS:
        logger.warning(
            "job_raw_text_truncated",
            original_chars=len(raw_text),
            truncated_to=MAX_RAW_TEXT_CHARS,
        )
        raw_text = raw_text[:MAX_RAW_TEXT_CHARS]

    user_message = (
        f"<job_posting>\n{raw_text}\n</job_posting>\n\n"
        "Extract the structured fields per the rules above."
    )
    result = await job_extractor.run(user_message)
    input_tokens, output_tokens = extract_token_usage(result.usage())
    usage_dict: dict[str, int | None] = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
    logger.info(
        "job_extraction_done",
        input_tokens=usage_dict["input_tokens"],
        output_tokens=usage_dict["output_tokens"],
        title=result.output.title,
        company=result.output.company,
        requirements=len(result.output.requirements),
    )
    return result.output, usage_dict


async def persist_job_extraction(
    session: AsyncSession,
    job_id: uuid.UUID,
    extraction: JobExtraction,
) -> None:
    """Update job fields, embed the summary, replace requirements, mark ready.

    Idempotent on retry: any existing requirements are deleted before the
    new set is inserted. Caller owns the transaction.
    """
    job = await repository.get_job(session, job_id)
    if job is None:
        raise RuntimeError(f"Job {job_id} not found")

    job.title = extraction.title
    job.company = extraction.company
    job.location = extraction.location
    job.remote_policy = extraction.remote_policy
    job.seniority = extraction.seniority
    job.tech_stack = list(extraction.tech_stack)
    job.salary_range = extraction.salary_range
    job.summary = extraction.summary
    job.raw_extraction = extraction.model_dump(mode="json")

    if extraction.summary:
        job.embedding = await get_embedding(extraction.summary)
        job.embedding_model = settings.EMBEDDING_MODEL
    else:
        job.embedding = None
        job.embedding_model = None

    await repository.delete_requirements_by_job(session, job_id)

    if extraction.requirements:
        req_embeddings = await get_embeddings([r.text for r in extraction.requirements])
        requirements = [
            JobRequirement(
                job_id=job_id,
                text=req.text,
                category=req.category,
                embedding=embedding,
                embedding_model=settings.EMBEDDING_MODEL,
            )
            for req, embedding in zip(extraction.requirements, req_embeddings, strict=True)
        ]
        await repository.add_requirements(session, requirements)

    job.status = JobStatus.ready


async def mark_job_failed(job_id: uuid.UUID, error_message: str) -> None:
    """Set job.status='failed' and persist error_message. Opens its own session.

    Called from the ARQ task's except handler — must not share a transaction
    with the failing one so the failure state survives the rollback.
    """
    async with SessionLocal() as session:
        job = await repository.get_job(session, job_id)
        if job is None:
            return
        job.status = JobStatus.failed
        job.error_message = error_message
        await session.commit()


# ----- CRUD + creation (router-facing; caller owns the transaction) -----


async def _ensure_url_unique(session: AsyncSession, user_id: uuid.UUID, url: str | None) -> None:
    """Raise :class:`DuplicateJobError` if the user already has a job for ``url``."""
    if url is None:
        return
    existing = await repository.get_by_url(session, user_id, url)
    if existing is not None:
        raise DuplicateJobError(existing.id)


async def create_job_from_text(
    session: AsyncSession, user_id: uuid.UUID, payload: CreateJobFromText
) -> Job:
    """Persist a pasted-text job in 'pending'. Caller commits + enqueues extraction.

    AI job import is a paid capability — gate before persisting/enqueuing.
    """
    await providers.get(BillingProvider).assert_paid_tier(user_id)
    await _ensure_url_unique(session, user_id, payload.source_url)
    job = Job(
        user_id=user_id,
        source_kind=JobSourceKind.pasted,
        raw_text=payload.raw_text,
        source_url=payload.source_url,
        status=JobStatus.pending,
    )
    return await repository.add_job(session, job)


async def create_job_from_url(
    session: AsyncSession, user_id: uuid.UUID, payload: CreateJobFromUrl
) -> Job:
    """Persist a URL-source job in 'pending'. Caller commits + enqueues scrape.

    AI job import is a paid capability — gate before persisting/enqueuing.
    """
    await providers.get(BillingProvider).assert_paid_tier(user_id)
    url = str(payload.source_url)
    await _ensure_url_unique(session, user_id, url)
    job = Job(
        user_id=user_id,
        source_kind=JobSourceKind.url,
        source_url=url,
        raw_text="",
        status=JobStatus.pending,
    )
    return await repository.add_job(session, job)


async def list_jobs(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    status: JobStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[Job]:
    return await repository.list_jobs(session, user_id, status=status, limit=limit, offset=offset)


async def get_job_with_requirements(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> Job | None:
    """Cross-module read backing :class:`~app.modules.jobs.protocols.JobProvider`."""
    return await repository.get_job_with_requirements(session, user_id, job_id)


async def delete_job(session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID) -> bool:
    return await repository.delete_job(session, user_id, job_id)


async def mark_for_retry(session: AsyncSession, job: Job) -> str:
    """Flip a failed job back to 'pending' and return the task name to enqueue.

    Raises :class:`JobNotRetriableError` unless the job is currently 'failed'.
    Caller commits.
    """
    if job.status != JobStatus.failed:
        raise JobNotRetriableError(
            f"Job status is '{job.status.value}'; only 'failed' jobs can be retried"
        )
    # Retry re-runs AI extraction, so it stays behind the paid-tier gate.
    await providers.get(BillingProvider).assert_paid_tier(job.user_id)
    job.status = JobStatus.pending
    job.error_message = None
    return "scrape_and_extract_job" if job.source_kind == JobSourceKind.url else "extract_job"


# ----- Task-phase transitions (worker-facing; caller owns the transaction) -----


async def begin_extraction(session: AsyncSession, job_id: uuid.UUID) -> str:
    """Mark 'extracting', clear the error, and return the job's raw_text."""
    job = await repository.get_job(session, job_id)
    if job is None:
        raise RuntimeError(f"Job {job_id} not found")
    job.status = JobStatus.extracting
    job.error_message = None
    return job.raw_text


async def begin_scrape(session: AsyncSession, job_id: uuid.UUID) -> str:
    """Mark 'scraping', clear the error, and return the job's source_url."""
    job = await repository.get_job(session, job_id)
    if job is None:
        raise RuntimeError(f"Job {job_id} not found")
    if not job.source_url:
        raise RuntimeError(f"Job {job_id} has no source_url")
    job.status = JobStatus.scraping
    job.error_message = None
    return job.source_url


async def scrape_job(url: str) -> str:
    """Headless-browser scrape of a job posting (no DB)."""
    return await scrape_job_posting(url)


async def persist_scraped_text(session: AsyncSession, job_id: uuid.UUID, raw_text: str) -> None:
    """Store scraped raw_text and advance the job to 'extracting'."""
    job = await repository.get_job(session, job_id)
    if job is None:
        raise RuntimeError(f"Job {job_id} not found after scrape")
    job.raw_text = raw_text
    job.status = JobStatus.extracting
