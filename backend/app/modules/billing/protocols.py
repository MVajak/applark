"""Cross-module billing surface.

The AI feature services charge/refund credits via ``providers.get(BillingProvider)``
rather than importing the billing service/repository directly. ``charge``/``refund``
own their own short transaction (no session param) so the credit lock is never held
across the feature's LLM call.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from app.modules.billing.config import Feature


class BillingProvider(Protocol):
    async def charge(self, user_id: uuid.UUID, feature: Feature) -> None: ...
    async def refund(self, user_id: uuid.UUID, feature: Feature) -> None: ...
    # Gate for AI intake (CV parsing / job import): raises if the user has no paid tier.
    async def assert_paid_tier(self, user_id: uuid.UUID) -> None: ...
