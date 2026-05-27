import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.interview_prep.models import InterviewPrepRun


async def create_run(
    session: AsyncSession,
    *,
    job_id: uuid.UUID,
    role_overview: str,
    likely_areas_of_focus: list[str],
    questions: list[dict[str, Any]],
    questions_to_ask_them: list[str],
    llm_model: str,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> InterviewPrepRun:
    run = InterviewPrepRun(
        job_id=job_id,
        role_overview=role_overview,
        likely_areas_of_focus=likely_areas_of_focus,
        questions=questions,
        questions_to_ask_them=questions_to_ask_them,
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
) -> InterviewPrepRun | None:
    stmt = (
        select(InterviewPrepRun)
        .where(InterviewPrepRun.job_id == job_id)
        .order_by(InterviewPrepRun.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
