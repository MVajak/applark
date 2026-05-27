"""Orchestrate cover-letter drafting from job + latest match + CV chunks."""

import json
import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import providers
from app.core.llm import LLM_MODEL_SMART, extract_token_usage
from app.modules.cover_letters import repository as cover_letters_repository
from app.modules.cover_letters.agent import cover_letter_drafter
from app.modules.cover_letters.models import CoverLetterDraft as CoverLetterDraftRow
from app.modules.cv.models import CVChunk
from app.modules.cv.protocols import CVProvider
from app.modules.cv.schemas import CVChunkType, CVDocumentKind
from app.modules.jobs.protocols import JobProvider
from app.modules.jobs.schemas import JobStatus
from app.modules.matching.protocols import MatchingProvider
from app.modules.matching.schemas import MatchExplanation

logger = structlog.get_logger(__name__)

# Limit chunks fed to the agent to keep the prompt focused. Top match
# strengths + the summary chunk easily fit in this budget.
MAX_CHUNKS_PER_DRAFT = 8


class NoMatchRunError(RuntimeError):
    """Drafting requires a prior MatchRun for the job; none exists."""


class CoverLetterPrerequisitesError(RuntimeError):
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
            {"text": req.text, "category": req.category.value} for req in job.requirements
        ],
    }


def _chunk_for_prompt(chunk: CVChunk) -> dict[str, Any]:
    return {
        "id": str(chunk.id),
        "content": chunk.content,
        "chunk_type": chunk.chunk_type.value,
        "metadata": chunk.metadata_,
    }


def _select_chunks(chunks: list[CVChunk], strength_ids: set[uuid.UUID]) -> list[CVChunk]:
    """Pick chunks the agent should see: strengths first, then summary, capped."""
    selected: list[CVChunk] = [c for c in chunks if c.id in strength_ids]
    already = {c.id for c in selected}

    summary_chunk = next((c for c in chunks if c.chunk_type == CVChunkType.summary), None)
    if summary_chunk is not None and summary_chunk.id not in already:
        selected.append(summary_chunk)

    return selected[:MAX_CHUNKS_PER_DRAFT]


async def generate_cover_letter(session: AsyncSession, job_id: uuid.UUID) -> CoverLetterDraftRow:
    """Draft a cover letter using the job, the latest match run, and the CV.

    Persists a :class:`CoverLetterDraft` row and returns it. Caller owns
    the transaction (the route commits).
    """
    job = await providers.get(JobProvider).get_job_with_requirements(session, job_id)
    if job is None:
        raise CoverLetterPrerequisitesError(f"Job {job_id} not found")
    if job.status != JobStatus.ready:
        raise CoverLetterPrerequisitesError(
            f"Job status is '{job.status.value}'; drafting needs 'ready'."
        )

    match_run = await providers.get(MatchingProvider).get_latest_for_job(session, job_id)
    if match_run is None:
        raise NoMatchRunError("Run match against your CV before generating a cover letter.")

    cv_doc = await providers.get(CVProvider).get_latest_document_with_chunks(
        session, kind=CVDocumentKind.cv
    )
    if cv_doc is None:
        raise CoverLetterPrerequisitesError(
            "No CV uploaded yet — upload one via POST /api/v1/cv/documents."
        )
    if not cv_doc.chunks:
        raise CoverLetterPrerequisitesError(
            f"CV {cv_doc.id} has no chunks — chunking may not have completed."
        )

    # Re-validate the JSONB details back into a typed model so we can read
    # strengths[*].cv_chunk_id as UUIDs without dict-key spelunking.
    explanation = MatchExplanation.model_validate(match_run.details)
    strength_ids = {s.cv_chunk_id for s in explanation.strengths}
    selected_chunks = _select_chunks(list(cv_doc.chunks), strength_ids)

    job_dict = _build_job_dict(job)
    chunks_list = [_chunk_for_prompt(c) for c in selected_chunks]
    candidate_name = cv_doc.candidate_name or "the candidate"

    user_prompt = f"""<candidate_name>{candidate_name}</candidate_name>

<job>{json.dumps(job_dict)}</job>

<chunks>{json.dumps(chunks_list)}</chunks>

Draft the cover letter per the rules in the system prompt."""

    result = await cover_letter_drafter.run(user_prompt)
    draft = result.output
    input_tokens, output_tokens = extract_token_usage(result.usage())

    word_count = len(draft.body.split())
    logger.info(
        "cover_letter_draft_done",
        job_id=str(job_id),
        match_run_id=str(match_run.id),
        word_count=word_count,
        referenced_chunks=len(draft.referenced_cv_chunk_ids),
        tone=draft.tone,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    return await cover_letters_repository.create_draft(
        session,
        job_id=job_id,
        match_run_id=match_run.id,
        subject=draft.subject,
        body=draft.body,
        referenced_chunks=[str(cid) for cid in draft.referenced_cv_chunk_ids],
        tone=draft.tone,
        llm_model=LLM_MODEL_SMART,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
