import uuid
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.jobs.models import Job, JobRequirement
from app.modules.jobs.schemas import JobStatus


async def add_job(session: AsyncSession, job: Job) -> Job:
    session.add(job)
    await session.flush()
    await session.refresh(job)
    return job


async def get_job(session: AsyncSession, job_id: uuid.UUID) -> Job | None:
    return await session.get(Job, job_id)


async def get_job_with_requirements(
    session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
) -> Job | None:
    stmt = (
        select(Job)
        .where(Job.id == job_id, Job.user_id == user_id)
        .options(selectinload(Job.requirements))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_url(session: AsyncSession, user_id: uuid.UUID, url: str) -> Job | None:
    stmt = select(Job).where(Job.user_id == user_id, Job.source_url == url)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_jobs(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    status: JobStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[Job]:
    stmt = (
        select(Job)
        .where(Job.user_id == user_id)
        .order_by(Job.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status is not None:
        stmt = stmt.where(Job.status == status)
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_job(session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID) -> bool:
    job = await session.get(Job, job_id)
    if job is None or job.user_id != user_id:
        return False
    await session.delete(job)
    return True


async def add_requirements(
    session: AsyncSession, requirements: Sequence[JobRequirement]
) -> Sequence[JobRequirement]:
    session.add_all(requirements)
    await session.flush()
    return requirements


async def list_requirements_by_job(
    session: AsyncSession, job_id: uuid.UUID
) -> Sequence[JobRequirement]:
    stmt = (
        select(JobRequirement)
        .where(JobRequirement.job_id == job_id)
        .order_by(JobRequirement.created_at.asc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_requirements_by_job(session: AsyncSession, job_id: uuid.UUID) -> int:
    """Hard-delete all requirements for a job. Used for retry idempotency."""
    result = await session.execute(delete(JobRequirement).where(JobRequirement.job_id == job_id))
    return int(result.rowcount)  # pyright: ignore  # CursorResult.rowcount exists at runtime
