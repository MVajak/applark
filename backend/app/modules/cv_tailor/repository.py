import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cv_tailor.models import CVTailorRun


async def create_run(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    job_summary: str,
    suggestions: list[dict[str, Any]],
    do_not_suggest: list[str],
    llm_model: str,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> CVTailorRun:
    run = CVTailorRun(
        user_id=user_id,
        job_id=job_id,
        job_summary=job_summary,
        suggestions=suggestions,
        do_not_suggest=do_not_suggest,
        llm_model=llm_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    session.add(run)
    await session.flush()
    await session.refresh(run)
    return run


async def get_latest_for_job(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> CVTailorRun | None:
    stmt = (
        select(CVTailorRun)
        .where(CVTailorRun.user_id == user_id, CVTailorRun.job_id == job_id)
        .order_by(CVTailorRun.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
