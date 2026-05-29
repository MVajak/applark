"""Cross-module protocol for the jobs domain."""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs.models import Job


class JobProvider(Protocol):
    async def get_job_with_requirements(
        self, session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
    ) -> Job | None: ...
