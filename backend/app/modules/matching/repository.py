import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.matching.models import MatchRun


async def create_match_run(
    session: AsyncSession,
    *,
    job_id: uuid.UUID,
    overall_score: float,
    summary: str,
    details: dict[str, Any],
    llm_model: str,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> MatchRun:
    run = MatchRun(
        job_id=job_id,
        overall_score=overall_score,
        summary=summary,
        details=details,
        llm_model=llm_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    session.add(run)
    await session.flush()
    await session.refresh(run)
    return run


async def get_latest_for_job(
    session: AsyncSession, job_id: uuid.UUID
) -> MatchRun | None:
    stmt = (
        select(MatchRun)
        .where(MatchRun.job_id == job_id)
        .order_by(MatchRun.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_history_for_job(
    session: AsyncSession, job_id: uuid.UUID
) -> Sequence[MatchRun]:
    stmt = (
        select(MatchRun)
        .where(MatchRun.job_id == job_id)
        .order_by(MatchRun.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()
