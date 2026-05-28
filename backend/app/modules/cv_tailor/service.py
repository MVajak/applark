"""Orchestrate CV-tailor suggestions from job + match + all CV chunks."""

import json
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import LLM_MODEL_SMART, extract_token_usage
from app.modules.cv_tailor import repository as cv_tailor_repository
from app.modules.cv_tailor.agent import cv_tailor
from app.modules.cv_tailor.models import CVTailorRun
from app.modules.matching.schemas import MatchExplanation
from app.modules.shared.feature_context import (
    build_job_dict,
    chunk_for_prompt,
    gather_match_feature_context,
)

logger = structlog.get_logger(__name__)


async def run_cv_tailor(session: AsyncSession, job_id: uuid.UUID) -> CVTailorRun:
    """Run the tailor agent and persist the result. Caller commits.

    Unlike the cover-letter flow, the agent is given the full CV chunk list
    — suggestions may touch unmatched chunks (deprioritise the cook job,
    rephrase the design-system line, etc.).
    """
    ctx = await gather_match_feature_context(
        session,
        job_id,
        needs_ready_subject="tailor",
        no_match_action="requesting tailor suggestions",
    )

    # Re-validate the JSONB blob back into a typed model so the prompt
    # contains the same shape the system prompt's examples assume.
    explanation = MatchExplanation.model_validate(ctx.match_run.details)

    job_dict = build_job_dict(ctx.job)
    match_dict = explanation.model_dump(mode="json")
    chunks_list = [chunk_for_prompt(c) for c in ctx.cv_doc.chunks]

    user_prompt = f"""<job>{json.dumps(job_dict)}</job>

<match_analysis>{json.dumps(match_dict)}</match_analysis>

<cv_chunks>{json.dumps(chunks_list)}</cv_chunks>

Produce CV tailor suggestions per the rules above. Reference chunks by their UUID in cv_chunk_id."""

    result = await cv_tailor.run(user_prompt)
    output = result.output
    input_tokens, output_tokens = extract_token_usage(result.usage())

    logger.info(
        "cv_tailor_run_done",
        job_id=str(job_id),
        match_run_id=str(ctx.match_run.id),
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


async def get_latest_for_job(session: AsyncSession, job_id: uuid.UUID) -> CVTailorRun | None:
    return await cv_tailor_repository.get_latest_for_job(session, job_id)
