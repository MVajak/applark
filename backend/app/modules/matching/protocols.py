"""Cross-module protocol for the matching domain."""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.matching.models import MatchRun


class MatchingProvider(Protocol):
    async def get_latest_for_job(
        self, session: AsyncSession, job_id: uuid.UUID
    ) -> MatchRun | None: ...
