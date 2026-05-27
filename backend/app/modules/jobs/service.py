import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.embeddings import get_embedding, get_embeddings
from app.modules.jobs import repository
from app.modules.jobs.agent import job_extractor
from app.modules.jobs.models import JobRequirement
from app.modules.jobs.schemas import JobExtraction, JobStatus

logger = structlog.get_logger(__name__)

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
    usage = result.usage()
    usage_dict: dict[str, int | None] = {
        "input_tokens": getattr(usage, "input_tokens", None)
        or getattr(usage, "request_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None)
        or getattr(usage, "response_tokens", None),
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
    """Update job fields, embed the summary, replace requirements.

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
