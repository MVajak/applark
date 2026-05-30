"""Billing catalog: tiers, per-feature credit costs/access, and credit packs.

Single source of truth for what each AI feature costs, which tiers unlock it, and
the one-time credit packs on sale. Tunable; payments are stubbed for now.
"""

from dataclasses import dataclass
from typing import Literal

Tier = Literal["none", "pro", "premium"]
PaidTier = Literal["pro", "premium"]

# The chargeable AI features (intake — CV parse / job extraction — is free).
Feature = Literal["matching", "cover_letters", "cv_tailor", "interview_prep"]

FEATURE_COST: dict[Feature, int] = {
    "matching": 2,
    "cover_letters": 1,
    "cv_tailor": 2,
    "interview_prep": 3,
}

# Which tiers unlock each feature.
FEATURE_TIERS: dict[Feature, frozenset[Tier]] = {
    "matching": frozenset({"pro", "premium"}),
    "cover_letters": frozenset({"pro", "premium"}),
    "cv_tailor": frozenset({"premium"}),
    "interview_prep": frozenset({"premium"}),
}

ALL_FEATURES: tuple[Feature, ...] = ("matching", "cover_letters", "cv_tailor", "interview_prep")

# Paid tiers in display order (cheapest first).
PAID_TIERS: tuple[PaidTier, ...] = ("pro", "premium")

# Monthly subscription price per paid tier (USD). A tier unlocks its AI features;
# running them still spends credits. Tunable; payments are stubbed for now.
TIER_PRICE_USD: dict[PaidTier, int] = {
    "pro": 9,
    "premium": 19,
}


@dataclass(frozen=True)
class CreditPack:
    id: str
    price_usd: int
    credits: int


# One-time credit packs (pixella-style). Stubbed checkout grants the credits.
CREDIT_PACKS: tuple[CreditPack, ...] = (
    CreditPack(id="starter", price_usd=5, credits=50),
    CreditPack(id="plus", price_usd=10, credits=110),
    CreditPack(id="max", price_usd=20, credits=240),
)


def is_paid_tier(tier: str) -> bool:
    """The one definition of "counts as a subscription" (gates AI intake)."""
    return tier in PAID_TIERS


def tier_unlocks(tier: str, feature: Feature) -> bool:
    return tier in FEATURE_TIERS[feature]


def feature_access(tier: str) -> dict[str, bool]:
    return {feature: tier_unlocks(tier, feature) for feature in ALL_FEATURES}


def feature_costs() -> dict[str, int]:
    return {feature: FEATURE_COST[feature] for feature in ALL_FEATURES}


def tier_features(tier: PaidTier) -> list[Feature]:
    """Features a tier unlocks, in display order."""
    return [feature for feature in ALL_FEATURES if tier_unlocks(tier, feature)]
