"""Orchestrate cover-letter drafting from job + latest match + CV chunks."""

import json
import uuid
from collections.abc import Sequence

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import LLM_MODEL_SMART, extract_token_usage
from app.modules.cover_letters import repository as cover_letters_repository
from app.modules.cover_letters.agent import cover_letter_drafter
from app.modules.cover_letters.models import CoverLetterDraft as CoverLetterDraftRow
from app.modules.cv.models import CVChunk
from app.modules.cv.schemas import CVChunkType
from app.modules.matching.schemas import MatchExplanation
from app.modules.shared.feature_context import (
    build_job_dict,
    chunk_for_prompt,
    gather_match_feature_context,
)

logger = structlog.get_logger(__name__)

# Limit chunks fed to the agent to keep the prompt focused. Top match
# strengths + the summary chunk easily fit in this budget.
MAX_CHUNKS_PER_DRAFT = 8


def _select_chunks(chunks: list[CVChunk], strength_ids: set[uuid.UUID]) -> list[CVChunk]:
    """Pick chunks the agent should see: strengths first, then summary, capped."""
    selected: list[CVChunk] = [c for c in chunks if c.id in strength_ids]
    already = {c.id for c in selected}

    summary_chunk = next((c for c in chunks if c.chunk_type == CVChunkType.summary), None)
    if summary_chunk is not None and summary_chunk.id not in already:
        selected.append(summary_chunk)

    return selected[:MAX_CHUNKS_PER_DRAFT]


async def generate_cover_letter(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> CoverLetterDraftRow:
    """Draft a cover letter using the job, the latest match run, and the CV.

    Persists a :class:`CoverLetterDraft` row and returns it. Caller owns
    the transaction (the route commits).
    """
    ctx = await gather_match_feature_context(
        session,
        user_id,
        job_id,
        needs_ready_subject="drafting",
        no_match_action="generating a cover letter",
    )

    # Re-validate the JSONB details back into a typed model so we can read
    # strengths[*].cv_chunk_id as UUIDs without dict-key spelunking.
    explanation = MatchExplanation.model_validate(ctx.match_run.details)
    strength_ids = {s.cv_chunk_id for s in explanation.strengths}
    selected_chunks = _select_chunks(list(ctx.cv_doc.chunks), strength_ids)

    job_dict = build_job_dict(ctx.job)
    chunks_list = [chunk_for_prompt(c) for c in selected_chunks]
    candidate_name = ctx.cv_doc.candidate_name or "the candidate"

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
        match_run_id=str(ctx.match_run.id),
        word_count=word_count,
        referenced_chunks=len(draft.referenced_cv_chunk_ids),
        tone=draft.tone,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    return await cover_letters_repository.create_draft(
        session,
        user_id=user_id,
        job_id=job_id,
        match_run_id=ctx.match_run.id,
        subject=draft.subject,
        body=draft.body,
        referenced_chunks=[str(cid) for cid in draft.referenced_cv_chunk_ids],
        tone=draft.tone,
        llm_model=LLM_MODEL_SMART,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


async def list_for_job(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> Sequence[CoverLetterDraftRow]:
    return await cover_letters_repository.list_for_job(session, user_id, job_id)
