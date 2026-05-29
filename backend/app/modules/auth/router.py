from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis

from app.core.database import SessionLocal
from app.core.redis import get_redis
from app.core.security import AuthUser, get_current_user
from app.modules.auth import service as auth_service
from app.modules.auth.schemas import (
    RefreshRequest,
    RequestOtp,
    RequestOtpResponse,
    TokenPair,
    UserRead,
    VerifyOtp,
)
from app.modules.auth.service import (
    InvalidOtpError,
    InvalidRefreshTokenError,
    OtpRequestThrottledError,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Generic, enumeration-safe response — identical whether or not the email is known.
_OTP_SENT_MESSAGE = "If that email can sign in, a code has been sent."


@router.post("/request-otp", response_model=RequestOtpResponse)
async def request_otp(
    payload: RequestOtp,
    redis: Annotated[Redis, Depends(get_redis)],
) -> RequestOtpResponse:
    async with SessionLocal() as session:
        try:
            await auth_service.request_otp(session, redis, payload.email)
        except OtpRequestThrottledError as exc:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
            ) from exc
        await session.commit()
    return RequestOtpResponse(message=_OTP_SENT_MESSAGE)


@router.post("/verify-otp", response_model=TokenPair)
async def verify_otp(payload: VerifyOtp) -> TokenPair:
    async with SessionLocal() as session:
        try:
            tokens = await auth_service.verify_otp(session, payload.email, payload.code)
        except InvalidOtpError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
        await session.commit()
    return tokens


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest) -> TokenPair:
    try:
        return await auth_service.refresh(payload.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/me", response_model=UserRead)
async def me(current_user: Annotated[AuthUser, Depends(get_current_user)]) -> UserRead:
    async with SessionLocal() as session:
        user = await auth_service.get_user(session, current_user.id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists"
        )
    return UserRead.model_validate(user)
