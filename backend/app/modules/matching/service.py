"""Deterministic prep + agent orchestration for matching.

Per PLAN.md §9.9, vector similarity / ranking is deterministic work and
stays out of the LLM. This module builds a :class:`MatchContext`, then
hands it to the explainer agent for the language-shaped part.
"""

import json
import uuid
from collections.abc import Sequence
from typing import Any

import structlog
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core import providers
from app.core.llm import LLM_MODEL_SMART, extract_token_usage
from app.modules.cv.models import CVChunk, CVDocument
from app.modules.cv.protocols import CVProvider
from app.modules.cv.schemas import CVDocumentKind
from app.modules.jobs.protocols import JobProvider
from app.modules.jobs.schemas import JobRead, JobStatus
from app.modules.matching import repository as matching_repository
from app.modules.matching.agent import match_explainer
from app.modules.matching.models import MatchRun

logger = structlog.get_logger(__name__)


class NoCVUploadedError(RuntimeError):
    """No CV document exists yet — matching can't run."""


class MissingEmbeddingsError(RuntimeError):
    """Job or CV chunks lack embeddings; extraction may not be finished."""


class JobNotFoundError(RuntimeError):
    """No job exists for the given id."""


class JobNotReadyError(RuntimeError):
    """The job exists but isn't 'ready', so matching can't run yet."""


# ----- Internal context types (passed to the agent, not the API) -----


class CandidateChunkWithScore(BaseModel):
    cv_chunk_id: uuid.UUID
    chunk_type: str
    content: str
    metadata: dict[str, Any]
    similarity: float


class RequirementMatch(BaseModel):
    requirement_id: uuid.UUID
    requirement_text: str
    category: str
    top_chunks: list[CandidateChunkWithScore]


class MatchContext(BaseModel):
    job: dict[str, Any]
    candidate_chunks: list[CandidateChunkWithScore]
    requirement_matches: list[RequirementMatch]


# ----- Builders -----


async def find_latest_cv(session: AsyncSession, user_id: uuid.UUID) -> CVDocument:
    """Return the user's most recent uploaded CV (kind='cv'), with chunks loaded."""
    doc = await providers.get(CVProvider).get_latest_document_with_chunks(
        session, user_id, kind=CVDocumentKind.cv
    )
    if doc is None:
        raise NoCVUploadedError("No CV uploaded yet — POST /api/v1/cv/documents first.")
    return doc


async def _top_chunks_by_embedding(
    session: AsyncSession,
    *,
    cv_document_id: uuid.UUID,
    target_embedding: list[float],
    limit: int,
) -> list[CandidateChunkWithScore]:
    """Return the ``limit`` CV chunks closest to ``target_embedding``.

    Uses pgvector cosine distance; similarity = 1 - distance.
    Scoped to a single CV document so we don't mix chunks across CVs.
    """
    distance_col = CVChunk.embedding.cosine_distance(target_embedding).label("distance")
    stmt = (
        select(CVChunk, distance_col)
        .where(CVChunk.document_id == cv_document_id)
        .order_by(distance_col)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [
        CandidateChunkWithScore(
            cv_chunk_id=chunk.id,
            chunk_type=chunk.chunk_type.value,
            content=chunk.content,
            metadata=chunk.metadata_,
            similarity=1.0 - float(distance),
        )
        for chunk, distance in result.all()
    ]


async def build_match_context(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> MatchContext:
    """Run all deterministic vector search and assemble the agent's input."""
    job = await providers.get(JobProvider).get_job_with_requirements(session, user_id, job_id)
    if job is None:
        raise JobNotFoundError("Job not found")
    if job.status != JobStatus.ready:
        raise JobNotReadyError(
            f"Job status is '{job.status.value}'; matching requires "
            "'ready'. Wait for extraction to finish or retry the job."
        )
    if job.embedding is None:
        raise MissingEmbeddingsError(
            f"Job {job_id} has no embedding — extraction may not have completed"
        )

    cv_doc = await find_latest_cv(session, user_id)
    if not cv_doc.chunks:
        raise MissingEmbeddingsError(
            f"CV {cv_doc.id} has no chunks — chunking may not have completed"
        )
    missing = [c for c in cv_doc.chunks if c.embedding is None]
    if missing:
        raise MissingEmbeddingsError(f"CV {cv_doc.id} has {len(missing)} chunks without embeddings")

    requirement_matches: list[RequirementMatch] = []
    for req in job.requirements:
        req_embedding: list[float] | None = req.embedding
        if req_embedding is None:
            # Skip requirements without embeddings — the agent gets the rest.
            continue
        top = await _top_chunks_by_embedding(
            session,
            cv_document_id=cv_doc.id,
            target_embedding=req_embedding,
            limit=3,
        )
        requirement_matches.append(
            RequirementMatch(
                requirement_id=req.id,
                requirement_text=req.text,
                category=req.category.value,
                top_chunks=top,
            )
        )

    candidate_chunks = await _top_chunks_by_embedding(
        session,
        cv_document_id=cv_doc.id,
        target_embedding=job.embedding,
        limit=8,
    )

    job_dict = JobRead.model_validate(job).model_dump(
        mode="json",
        exclude={"raw_text", "requirements"},
    )

    return MatchContext(
        job=job_dict,
        candidate_chunks=candidate_chunks,
        requirement_matches=requirement_matches,
    )


async def run_match(session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID) -> MatchRun:
    """Build context, call the explainer, persist the run. Caller commits."""
    context = await build_match_context(session, user_id, job_id)

    user_prompt = f"""<job>
{json.dumps(context.job, indent=2)}
</job>

<candidate_chunks>
{json.dumps([c.model_dump(mode="json") for c in context.candidate_chunks], indent=2)}
</candidate_chunks>

<requirement_matches>
{json.dumps([r.model_dump(mode="json") for r in context.requirement_matches], indent=2)}
</requirement_matches>

Now produce a MatchExplanation per the rules in the system prompt."""

    result = await match_explainer.run(user_prompt)
    explanation = result.output
    input_tokens, output_tokens = extract_token_usage(result.usage())

    logger.info(
        "match_run_done",
        job_id=str(job_id),
        overall_score=explanation.overall_score,
        strengths=len(explanation.strengths),
        gaps=len(explanation.gaps),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    return await matching_repository.create_match_run(
        session,
        user_id=user_id,
        job_id=job_id,
        overall_score=explanation.overall_score,
        summary=explanation.summary,
        details=explanation.model_dump(mode="json"),
        llm_model=LLM_MODEL_SMART,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


async def get_latest_for_job(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> MatchRun | None:
    """Cross-module read backing :class:`~app.modules.matching.protocols.MatchingProvider`."""
    return await matching_repository.get_latest_for_job(session, user_id, job_id)


async def get_history_for_job(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> Sequence[MatchRun]:
    return await matching_repository.get_history_for_job(session, user_id, job_id)


__all__ = [
    "CandidateChunkWithScore",
    "JobNotFoundError",
    "JobNotReadyError",
    "MatchContext",
    "MissingEmbeddingsError",
    "NoCVUploadedError",
    "RequirementMatch",
    "build_match_context",
    "find_latest_cv",
    "get_history_for_job",
    "get_latest_for_job",
    "run_match",
]
