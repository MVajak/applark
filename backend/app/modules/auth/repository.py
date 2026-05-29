import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import OtpCode, User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await session.get(User, user_id)


async def create_user(session: AsyncSession, email: str) -> User:
    user = User(email=email)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def create_otp(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    code_hash: str,
    expires_at: datetime,
) -> OtpCode:
    otp = OtpCode(user_id=user_id, code_hash=code_hash, expires_at=expires_at)
    session.add(otp)
    await session.flush()
    return otp


async def get_latest_valid_otp(
    session: AsyncSession, user_id: uuid.UUID, now: datetime
) -> OtpCode | None:
    """Most recent unused, unexpired OTP for the user (if any)."""
    stmt = (
        select(OtpCode)
        .where(
            OtpCode.user_id == user_id,
            OtpCode.used_at.is_(None),
            OtpCode.expires_at > now,
        )
        .order_by(OtpCode.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def invalidate_pending_otps(session: AsyncSession, user_id: uuid.UUID, now: datetime) -> None:
    """Mark all of a user's unused OTPs as used, so a fresh request supersedes them."""
    await session.execute(
        update(OtpCode)
        .where(OtpCode.user_id == user_id, OtpCode.used_at.is_(None))
        .values(used_at=now)
    )
