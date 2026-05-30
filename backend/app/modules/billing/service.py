"""Billing logic: status, per-feature charge/refund, and (stub) subscribe/checkout.

`charge`/`refund` own a short locked transaction so the credit row lock is never held
across an LLM call — feature services call them via ``BillingProvider`` around the agent.
`get_status`/`subscribe`/`grant_pack` are driven by the billing router and take its session.
"""

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.modules.billing import repository
from app.modules.billing.config import (
    CREDIT_PACKS,
    FEATURE_COST,
    PAID_TIERS,
    TIER_PRICE_USD,
    Feature,
    PaidTier,
    feature_access,
    feature_costs,
    is_paid_tier,
    tier_features,
    tier_unlocks,
)
from app.modules.billing.schemas import BillingStatus, PlanRead

logger = structlog.get_logger(__name__)


class UserNotFoundError(RuntimeError):
    """No user row for the given id."""


class FeatureNotInTierError(RuntimeError):
    """The user's tier does not unlock the requested feature (→ 403)."""


class InsufficientCreditsError(RuntimeError):
    """The user lacks enough credits to run the feature (→ 402)."""


class UnknownPackError(RuntimeError):
    """No credit pack with the given id."""


class SubscriptionRequiredError(RuntimeError):
    """An action requires an active paid tier — subscribe first (→ 403).

    Used both for buying credits and for AI intake (CV parsing / job import).
    """


async def get_status(session: AsyncSession, user_id: uuid.UUID) -> BillingStatus:
    user = await repository.get_user(session, user_id)
    if user is None:
        raise UserNotFoundError(f"User {user_id} not found")
    return BillingStatus(
        tier=user.tier,
        credits=user.credits,
        access=feature_access(user.tier),
        costs=feature_costs(),
    )


def list_plans() -> list[PlanRead]:
    """The purchasable subscription tiers — price + the AI features they unlock."""
    return [
        PlanRead(tier=tier, price_usd=TIER_PRICE_USD[tier], features=list(tier_features(tier)))
        for tier in PAID_TIERS
    ]


async def assert_paid_tier(user_id: uuid.UUID) -> None:
    """Raise :class:`SubscriptionRequiredError` unless the user is on a paid tier.

    Gates AI intake (CV parsing, job import) — covered by the subscription, not
    credits. Owns its own short read session so callers (the cv/jobs services)
    reach it only through ``BillingProvider``, never the billing repo/service.
    """
    async with SessionLocal() as session:
        user = await repository.get_user(session, user_id)
    if user is None:
        raise UserNotFoundError(f"User {user_id} not found")
    if not is_paid_tier(user.tier):
        raise SubscriptionRequiredError("Subscribe to a plan to use AI features.")


async def charge(user_id: uuid.UUID, feature: Feature) -> None:
    """Deduct the feature's cost in its own locked transaction (pay-before-use).

    Raises :class:`FeatureNotInTierError` / :class:`InsufficientCreditsError`.
    """
    cost = FEATURE_COST[feature]
    async with SessionLocal() as session:
        user = await repository.lock_user(session, user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        if not tier_unlocks(user.tier, feature):
            raise FeatureNotInTierError("Your plan doesn't include this feature.")
        if user.credits < cost:
            raise InsufficientCreditsError("Not enough credits — buy more to continue.")
        await repository.apply_delta(session, user, delta=-cost, reason="use", feature=feature)
        await session.commit()
    logger.info("credits_charged", user_id=str(user_id), feature=feature, cost=cost)


async def refund(user_id: uuid.UUID, feature: Feature) -> None:
    """Return a feature's cost (own transaction) — used when the agent call fails."""
    cost = FEATURE_COST[feature]
    async with SessionLocal() as session:
        user = await repository.lock_user(session, user_id)
        if user is None:
            return
        await repository.apply_delta(session, user, delta=cost, reason="refund", feature=feature)
        await session.commit()
    logger.info("credits_refunded", user_id=str(user_id), feature=feature, cost=cost)


async def subscribe(session: AsyncSession, user_id: uuid.UUID, tier: PaidTier) -> None:
    """Stub 'subscribe': set the user's access tier. Caller commits."""
    user = await repository.lock_user(session, user_id)
    if user is None:
        raise UserNotFoundError(f"User {user_id} not found")
    await repository.set_tier(session, user, tier)


async def grant_pack(session: AsyncSession, user_id: uuid.UUID, pack_id: str) -> None:
    """Stub 'checkout': grant a credit pack's credits. Caller commits.

    Credits are only usable on a paid tier, so a free (``none``) user must
    subscribe before topping up — otherwise they'd buy an unspendable balance.
    """
    pack = next((p for p in CREDIT_PACKS if p.id == pack_id), None)
    if pack is None:
        raise UnknownPackError(f"Unknown credit pack '{pack_id}'")
    user = await repository.lock_user(session, user_id)
    if user is None:
        raise UserNotFoundError(f"User {user_id} not found")
    if not is_paid_tier(user.tier):
        raise SubscriptionRequiredError("Subscribe to a plan before buying credits.")
    await repository.apply_delta(session, user, delta=pack.credits, reason="purchase")
