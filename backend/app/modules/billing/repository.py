import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.billing.models import CreditLedger


async def get_user(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await session.get(User, user_id)


async def lock_user(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Row-locked load (`SELECT … FOR UPDATE`) so concurrent charges can't overspend."""
    result = await session.execute(select(User).where(User.id == user_id).with_for_update())
    return result.scalar_one_or_none()


async def apply_delta(
    session: AsyncSession,
    user: User,
    *,
    delta: int,
    reason: str,
    feature: str | None = None,
) -> None:
    """Adjust the user's balance and append a ledger row. Caller owns the transaction."""
    user.credits += delta
    session.add(
        CreditLedger(
            user_id=user.id,
            delta=delta,
            balance_after=user.credits,
            reason=reason,
            feature=feature,
        )
    )
    await session.flush()


async def set_tier(session: AsyncSession, user: User, tier: str) -> None:
    user.tier = tier
    await session.flush()
