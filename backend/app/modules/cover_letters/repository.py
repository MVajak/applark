import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cover_letters.models import CoverLetterDraft


async def create_draft(
    session: AsyncSession,
    *,
    job_id: uuid.UUID,
    match_run_id: uuid.UUID | None,
    subject: str,
    body: str,
    referenced_chunks: list[str],
    tone: str | None,
    llm_model: str,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> CoverLetterDraft:
    draft = CoverLetterDraft(
        job_id=job_id,
        match_run_id=match_run_id,
        subject=subject,
        body=body,
        referenced_chunks=referenced_chunks,
        tone=tone,
        llm_model=llm_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    session.add(draft)
    await session.flush()
    await session.refresh(draft)
    return draft


async def list_for_job(
    session: AsyncSession, job_id: uuid.UUID
) -> Sequence[CoverLetterDraft]:
    stmt = (
        select(CoverLetterDraft)
        .where(CoverLetterDraft.job_id == job_id)
        .order_by(CoverLetterDraft.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()
