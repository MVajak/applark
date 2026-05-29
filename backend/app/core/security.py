"""JWT issuance/verification, OTP hashing, and the auth dependency.

OTP codes are stored only as a keyed HMAC (peppered with ``OTP_PEPPER``), so a
read of the database alone can't reverse the 6-digit code without the app secret.
JWTs are signed (HS256) and stateless — nothing is persisted server-side.
"""

from __future__ import annotations

import hmac
import uuid
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Annotated, Literal

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ValidationError

from app.core.config import settings

_ALGORITHM = "HS256"

TokenType = Literal["access", "refresh"]


class TokenClaims(BaseModel):
    sub: uuid.UUID
    email: str
    type: TokenType
    iat: int
    exp: int


class AuthUser(BaseModel):
    """The signed-in identity resolved from a valid access token (no DB hit)."""

    id: uuid.UUID
    email: str


class TokenError(Exception):
    """A JWT was missing, malformed, expired, or of the wrong type."""


# ----- OTP hashing -----


def hash_otp(code: str) -> str:
    """Keyed HMAC-SHA256 of an OTP code (peppered, so a DB leak alone is useless)."""
    return hmac.new(settings.OTP_PEPPER.encode(), code.encode(), sha256).hexdigest()


def verify_otp_hash(code: str, code_hash: str) -> bool:
    """Constant-time comparison of a submitted code against the stored hash."""
    return hmac.compare_digest(hash_otp(code), code_hash)


# ----- JWT -----


def _create_token(user_id: uuid.UUID, email: str, token_type: TokenType, ttl: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=_ALGORITHM)


def create_access_token(user_id: uuid.UUID, email: str) -> str:
    ttl = timedelta(minutes=settings.JWT_ACCESS_TTL_MINUTES)
    return _create_token(user_id, email, "access", ttl)


def create_refresh_token(user_id: uuid.UUID, email: str) -> str:
    ttl = timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    return _create_token(user_id, email, "refresh", ttl)


def decode_token(token: str, expected_type: TokenType) -> TokenClaims:
    """Verify signature + expiry and the token's ``type``. Raises :class:`TokenError`."""
    try:
        decoded: object = jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
    try:
        claims = TokenClaims.model_validate(decoded)
    except ValidationError as exc:
        raise TokenError("malformed token claims") from exc
    if claims.type != expected_type:
        raise TokenError(f"expected {expected_type} token, got {claims.type}")
    return claims


# ----- FastAPI dependency -----

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = decode_token(credentials.credentials, "access")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return AuthUser(id=claims.sub, email=claims.email)


async def get_current_user_query(token: str | None = None) -> AuthUser:
    """Auth via a ``?token=`` query param — for SSE/EventSource, which can't set headers."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        claims = decode_token(token, "access")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc
    return AuthUser(id=claims.sub, email=claims.email)
