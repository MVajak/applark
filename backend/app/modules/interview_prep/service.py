"""Orchestrate interview-prep generation from job + match + all CV chunks."""

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
from app.modules.interview_prep import repository as interview_prep_repository
from app.modules.interview_prep.agent import interview_prep_agent
from app.modules.interview_prep.models import InterviewPrepRun
from app.modules.jobs.protocols import JobProvider
from app.modules.jobs.schemas import JobStatus
from app.modules.matching.protocols import MatchingProvider
from app.modules.matching.schemas import MatchExplanation

logger = structlog.get_logger(__name__)


class NoMatchRunError(RuntimeError):
    """Interview prep requires a prior MatchRun; none exists."""


class InterviewPrepPrerequisitesError(RuntimeError):
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


async def generate_interview_prep(
    session: AsyncSession, job_id: uuid.UUID
) -> InterviewPrepRun:
    """Generate interview prep and persist it. Caller commits.

    The agent gets ALL CV chunks (not a top-k subset) because any chunk
    might be the right anchor for a question's suggested_angle.
    """
    job = await providers.get(JobProvider).get_job_with_requirements(session, job_id)
    if job is None:
        raise InterviewPrepPrerequisitesError(f"Job {job_id} not found")
    if job.status != JobStatus.ready:
        raise InterviewPrepPrerequisitesError(
            f"Job status is '{job.status.value}'; interview prep needs 'ready'."
        )

    match_run = await providers.get(MatchingProvider).get_latest_for_job(session, job_id)
    if match_run is None:
        raise NoMatchRunError(
            "Run match against your CV before generating interview prep."
        )

    cv_doc = await providers.get(CVProvider).get_latest_document_with_chunks(
        session, kind=CVDocumentKind.cv
    )
    if cv_doc is None:
        raise InterviewPrepPrerequisitesError(
            "No CV uploaded yet — upload one via POST /api/v1/cv/documents."
        )
    if not cv_doc.chunks:
        raise InterviewPrepPrerequisitesError(
            f"CV {cv_doc.id} has no chunks — chunking may not have completed."
        )

    explanation = MatchExplanation.model_validate(match_run.details)

    job_dict = _build_job_dict(job)
    match_dict = explanation.model_dump(mode="json")
    chunks_list = [_chunk_for_prompt(c) for c in cv_doc.chunks]

    user_prompt = f"""<job>{json.dumps(job_dict)}</job>

<match_analysis>{json.dumps(match_dict)}</match_analysis>

<cv_chunks>{json.dumps(chunks_list)}</cv_chunks>

Generate interview prep per the rules above. Reference chunks by their UUID in
referenced_cv_chunk_ids when the candidate has relevant experience for a question."""

    result = await interview_prep_agent.run(user_prompt)
    output = result.output
    usage = result.usage()
    input_tokens = getattr(usage, "input_tokens", None) or getattr(
        usage, "request_tokens", None
    )
    output_tokens = getattr(usage, "output_tokens", None) or getattr(
        usage, "response_tokens", None
    )

    logger.info(
        "interview_prep_done",
        job_id=str(job_id),
        match_run_id=str(match_run.id),
        questions=len(output.questions),
        areas_of_focus=len(output.likely_areas_of_focus),
        questions_to_ask=len(output.questions_to_ask_them),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    return await interview_prep_repository.create_run(
        session,
        job_id=job_id,
        role_overview=output.role_overview,
        likely_areas_of_focus=list(output.likely_areas_of_focus),
        questions=[q.model_dump(mode="json") for q in output.questions],
        questions_to_ask_them=list(output.questions_to_ask_them),
        llm_model=LLM_MODEL_SMART,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
