"""Orchestrate CV-tailor suggestions from job + match + all CV chunks."""

import json
import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import providers
from app.core.llm import LLM_MODEL_SMART
from app.modules.cv.models import CVChunk
from app.modules.cv.protocols import CVProvider
from app.modules.cv.schemas import CVDocumentKind
from app.modules.cv_tailor import repository as cv_tailor_repository
from app.modules.cv_tailor.agent import cv_tailor
from app.modules.cv_tailor.models import CVTailorRun
from app.modules.jobs.protocols import JobProvider
from app.modules.jobs.schemas import JobStatus
from app.modules.matching.protocols import MatchingProvider
from app.modules.matching.schemas import MatchExplanation

logger = structlog.get_logger(__name__)


class NoMatchRunError(RuntimeError):
    """Tailor suggestions require a prior MatchRun; none exists."""


class CVTailorPrerequisitesError(RuntimeError):
    """Job isn't ready, no CV uploaded, or CV has no chunks."""


def _build_job_dict(job: Any) -> dict[str, Any]:
    return {
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "remote_policy": job.remote_policy.value,
        "seniority": job.seniority.value,
        "tech_stack": list(job.tech_stack),
        "summary": job.summary,
        "requirements": [
            {"text": req.text, "category": req.category.value}
            for req in job.requirements
        ],
    }


def _chunk_for_prompt(chunk: CVChunk) -> dict[str, Any]:
    return {
        "id": str(chunk.id),
        "content": chunk.content,
        "chunk_type": chunk.chunk_type.value,
        "metadata": chunk.metadata_,
    }


async def run_cv_tailor(
    session: AsyncSession, job_id: uuid.UUID
) -> CVTailorRun:
    """Run the tailor agent and persist the result. Caller commits.

    Unlike the cover-letter flow, the agent is given the full CV chunk list
    — suggestions may touch unmatched chunks (deprioritise the cook job,
    rephrase the design-system line, etc.).
    """
    job = await providers.get(JobProvider).get_job_with_requirements(session, job_id)
    if job is None:
        raise CVTailorPrerequisitesError(f"Job {job_id} not found")
    if job.status != JobStatus.ready:
        raise CVTailorPrerequisitesError(
            f"Job status is '{job.status.value}'; tailor needs 'ready'."
        )

    match_run = await providers.get(MatchingProvider).get_latest_for_job(session, job_id)
    if match_run is None:
        raise NoMatchRunError(
            "Run match against your CV before requesting tailor suggestions."
        )

    cv_doc = await providers.get(CVProvider).get_latest_document_with_chunks(
        session, kind=CVDocumentKind.cv
    )
    if cv_doc is None:
        raise CVTailorPrerequisitesError(
            "No CV uploaded yet — upload one via POST /api/v1/cv/documents."
        )
    if not cv_doc.chunks:
        raise CVTailorPrerequisitesError(
            f"CV {cv_doc.id} has no chunks — chunking may not have completed."
        )

    # Re-validate the JSONB blob back into a typed model so the prompt
    # contains the same shape the system prompt's examples assume.
    explanation = MatchExplanation.model_validate(match_run.details)

    job_dict = _build_job_dict(job)
    match_dict = explanation.model_dump(mode="json")
    chunks_list = [_chunk_for_prompt(c) for c in cv_doc.chunks]

    user_prompt = f"""<job>{json.dumps(job_dict)}</job>

<match_analysis>{json.dumps(match_dict)}</match_analysis>

<cv_chunks>{json.dumps(chunks_list)}</cv_chunks>

Produce CV tailor suggestions per the rules above. Reference chunks by their UUID in cv_chunk_id."""

    result = await cv_tailor.run(user_prompt)
    output = result.output
    usage = result.usage()
    input_tokens = getattr(usage, "input_tokens", None) or getattr(
        usage, "request_tokens", None
    )
    output_tokens = getattr(usage, "output_tokens", None) or getattr(
        usage, "response_tokens", None
    )

    logger.info(
        "cv_tailor_run_done",
        job_id=str(job_id),
        match_run_id=str(match_run.id),
        suggestions=len(output.suggestions),
        do_not_suggest=len(output.do_not_suggest),
        chunks_input=len(chunks_list),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    return await cv_tailor_repository.create_run(
        session,
        job_id=job_id,
        job_summary=output.job_summary,
        suggestions=[s.model_dump(mode="json") for s in output.suggestions],
        do_not_suggest=list(output.do_not_suggest),
        llm_model=LLM_MODEL_SMART,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
