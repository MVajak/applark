"""Auth flow orchestration: request OTP → verify → issue tokens, and refresh.

The 6-digit code is generated with :mod:`secrets`, stored only as a peppered HMAC
(:func:`app.core.security.hash_otp`), delivered via an :class:`EmailSender`, and
guarded by a TTL, single-use, per-code attempt cap, and a Redis request rate-limit.
"""

import secrets
import uuid
from datetime import UTC, datetime, timedelta

import structlog
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_otp,
    verify_otp_hash,
)
from app.modules.auth import repository
from app.modules.auth.email import ConsoleEmailSender, EmailSender
from app.modules.auth.models import User
from app.modules.auth.schemas import TokenPair

logger = structlog.get_logger(__name__)

# Swap for a real provider (Resend/SMTP) implementing EmailSender — nothing else changes.
email_sender: EmailSender = ConsoleEmailSender()


class OtpRequestThrottledError(RuntimeError):
    """Too many OTP requests for this email in the rate-limit window."""


class InvalidOtpError(RuntimeError):
    """The submitted code is wrong, expired, already used, or out of attempts."""


class InvalidRefreshTokenError(RuntimeError):
    """The refresh token is missing, malformed, expired, or the wrong type."""


async def _enforce_request_rate_limit(redis: Redis, email: str) -> None:
    key = f"otp:req:{email.lower()}"
    count = int(await redis.incr(key))
    if count == 1:
        await redis.expire(key, 3600)
    if count > settings.OTP_REQUEST_LIMIT_PER_HOUR:
        raise OtpRequestThrottledError("Too many code requests — try again later.")


async def request_otp(session: AsyncSession, redis: Redis, email: str) -> None:
    """Find/create the user, supersede pending codes, store a fresh hashed code, send it."""
    await _enforce_request_rate_limit(redis, email)

    user = await repository.get_user_by_email(session, email)
    if user is None:
        user = await repository.create_user(session, email)

    now = datetime.now(UTC)
    await repository.invalidate_pending_otps(session, user.id, now)

    code = f"{secrets.randbelow(10**6):06d}"
    expires_at = now + timedelta(minutes=settings.OTP_TTL_MINUTES)
    await repository.create_otp(
        session, user_id=user.id, code_hash=hash_otp(code), expires_at=expires_at
    )
    await email_sender.send_otp(email, code)


async def verify_otp(session: AsyncSession, email: str, code: str) -> TokenPair:
    """Validate the latest live code and issue an access/refresh pair. Caller commits."""
    user = await repository.get_user_by_email(session, email)
    if user is None:
        raise InvalidOtpError("Invalid or expired code.")

    now = datetime.now(UTC)
    otp = await repository.get_latest_valid_otp(session, user.id, now)
    if otp is None:
        raise InvalidOtpError("Invalid or expired code.")

    if not verify_otp_hash(code, otp.code_hash):
        otp.attempt_count += 1
        if otp.attempt_count >= settings.OTP_MAX_ATTEMPTS:
            otp.used_at = now  # burn it after too many wrong guesses
        raise InvalidOtpError("Invalid or expired code.")

    otp.used_at = now
    return _issue_tokens(user.id, user.email)


async def refresh(refresh_token: str) -> TokenPair:
    """Verify a refresh token and mint a new pair (stateless — no DB needed)."""
    try:
        claims = decode_token(refresh_token, "refresh")
    except TokenError as exc:
        raise InvalidRefreshTokenError("Invalid refresh token.") from exc
    return _issue_tokens(claims.sub, claims.email)


def _issue_tokens(user_id: uuid.UUID, email: str) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user_id, email),
        refresh_token=create_refresh_token(user_id, email),
    )


async def get_user(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await repository.get_user(session, user_id)
