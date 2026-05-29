"""Shared gather/serialize helpers for match-derived LLM features.

`cover_letters`, `cv_tailor`, and `interview_prep` all run an LLM feature on
top of a job + its latest match run + the latest CV. They share the same
prerequisite loading, the same guard checks, and the same job/chunk JSON
shapes. Those live here so the three services only own what actually differs
(prompt assembly and chunk selection).

`matching` is deliberately NOT routed through here — it produces the match
itself via pgvector search and has no match-run dependency.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import providers
from app.modules.cv.models import CVChunk, CVDocument
from app.modules.cv.protocols import CVProvider
from app.modules.cv.schemas import CVDocumentKind
from app.modules.jobs.models import Job
from app.modules.jobs.protocols import JobProvider
from app.modules.jobs.schemas import JobStatus
from app.modules.matching.models import MatchRun
from app.modules.matching.protocols import MatchingProvider


class NoMatchRunError(RuntimeError):
    """The feature requires a prior MatchRun for the job; none exists."""


class FeaturePrerequisitesError(RuntimeError):
    """Job isn't ready, no CV uploaded, or the CV has no chunks."""


@dataclass(frozen=True)
class FeatureContext:
    """The three rows every match-derived feature needs, loaded and guarded."""

    job: Job
    match_run: MatchRun
    cv_doc: CVDocument


def build_job_dict(job: Job) -> dict[str, object]:
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


def chunk_for_prompt(chunk: CVChunk) -> dict[str, object]:
    return {
        "id": str(chunk.id),
        "content": chunk.content,
        "chunk_type": chunk.chunk_type.value,
        "metadata": chunk.metadata_,
    }


async def gather_match_feature_context(
    session: AsyncSession,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    *,
    needs_ready_subject: str,
    no_match_action: str,
) -> FeatureContext:
    """Load + guard the job, its latest match run, and the latest CV.

    ``needs_ready_subject`` and ``no_match_action`` only shape the user-facing
    409 wording (e.g. ``"drafting"`` / ``"generating a cover letter"``).

    Raises :class:`FeaturePrerequisitesError` if the job is missing, not
    ``ready``, or no CV with chunks exists; :class:`NoMatchRunError` if the job
    has never been matched.
    """
    job = await providers.get(JobProvider).get_job_with_requirements(session, user_id, job_id)
    if job is None:
        raise FeaturePrerequisitesError(f"Job {job_id} not found")
    if job.status != JobStatus.ready:
        raise FeaturePrerequisitesError(
            f"Job status is '{job.status.value}'; {needs_ready_subject} needs 'ready'."
        )

    match_run = await providers.get(MatchingProvider).get_latest_for_job(session, user_id, job_id)
    if match_run is None:
        raise NoMatchRunError(f"Run match against your CV before {no_match_action}.")

    cv_doc = await providers.get(CVProvider).get_latest_document_with_chunks(
        session, user_id, kind=CVDocumentKind.cv
    )
    if cv_doc is None:
        raise FeaturePrerequisitesError(
            "No CV uploaded yet — upload one via POST /api/v1/cv/documents."
        )
    if not cv_doc.chunks:
        raise FeaturePrerequisitesError(
            f"CV {cv_doc.id} has no chunks — chunking may not have completed."
        )

    return FeatureContext(job=job, match_run=match_run, cv_doc=cv_doc)


__all__ = [
    "FeatureContext",
    "FeaturePrerequisitesError",
    "NoMatchRunError",
    "build_job_dict",
    "chunk_for_prompt",
    "gather_match_feature_context",
]
