"""Orchestrate interview-prep generation from job + match + all CV chunks."""

import json
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import providers
from app.core.llm import LLM_MODEL_SMART, extract_token_usage
from app.modules.billing.protocols import BillingProvider
from app.modules.interview_prep import repository as interview_prep_repository
from app.modules.interview_prep.agent import interview_prep_agent
from app.modules.interview_prep.models import InterviewPrepRun
from app.modules.matching.schemas import MatchExplanation
from app.modules.shared.feature_context import (
    build_job_dict,
    chunk_for_prompt,
    gather_match_feature_context,
)

logger = structlog.get_logger(__name__)


async def generate_interview_prep(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> InterviewPrepRun:
    """Generate interview prep and persist it. Caller commits.

    The agent gets ALL CV chunks (not a top-k subset) because any chunk
    might be the right anchor for a question's suggested_angle.
    """
    ctx = await gather_match_feature_context(
        session,
        user_id,
        job_id,
        needs_ready_subject="interview prep",
        no_match_action="generating interview prep",
    )

    explanation = MatchExplanation.model_validate(ctx.match_run.details)

    job_dict = build_job_dict(ctx.job)
    match_dict = explanation.model_dump(mode="json")
    chunks_list = [chunk_for_prompt(c) for c in ctx.cv_doc.chunks]

    user_prompt = f"""<job>{json.dumps(job_dict)}</job>

<match_analysis>{json.dumps(match_dict)}</match_analysis>

<cv_chunks>{json.dumps(chunks_list)}</cv_chunks>

Generate interview prep per the rules above. Reference chunks by their UUID in
referenced_cv_chunk_ids when the candidate has relevant experience for a question."""

    billing = providers.get(BillingProvider)
    await billing.charge(user_id, "interview_prep")
    try:
        result = await interview_prep_agent.run(user_prompt)
    except Exception:
        await billing.refund(user_id, "interview_prep")
        raise
    output = result.output
    input_tokens, output_tokens = extract_token_usage(result.usage())

    logger.info(
        "interview_prep_done",
        job_id=str(job_id),
        match_run_id=str(ctx.match_run.id),
        questions=len(output.questions),
        areas_of_focus=len(output.likely_areas_of_focus),
        questions_to_ask=len(output.questions_to_ask_them),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    return await interview_prep_repository.create_run(
        session,
        user_id=user_id,
        job_id=job_id,
        role_overview=output.role_overview,
        likely_areas_of_focus=list(output.likely_areas_of_focus),
        questions=[q.model_dump(mode="json") for q in output.questions],
        questions_to_ask_them=list(output.questions_to_ask_them),
        llm_model=LLM_MODEL_SMART,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


async def get_latest_for_job(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> InterviewPrepRun | None:
    return await interview_prep_repository.get_latest_for_job(session, user_id, job_id)
