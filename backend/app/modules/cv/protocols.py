"""Cross-module protocol for the CV domain.

Other modules (matching, cover_letters, cv_tailor, interview_prep)
depend on this protocol rather than importing
`app.modules.cv.service` directly. The concrete service is registered
as the `CVProvider` implementation at startup (`app.main`), so
production code resolves it via `providers.get(CVProvider)` and never
touches the cv repository from outside the cv service.

Tests can swap in a fake implementation by re-registering.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cv.models import CVDocument
from app.modules.cv.schemas import CVDocumentKind


class CVProvider(Protocol):
    async def get_latest_document_with_chunks(
        self,
        session: AsyncSession,
        *,
        kind: CVDocumentKind | None = None,
    ) -> CVDocument | None: ...
