from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import SessionLocal
from app.core.security import AuthUser, get_current_user
from app.modules.billing import service as billing_service
from app.modules.billing.config import CREDIT_PACKS
from app.modules.billing.schemas import (
    BillingStatus,
    CheckoutRequest,
    CreditPackRead,
    PlanRead,
    SubscribeRequest,
)
from app.modules.billing.service import UnknownPackError

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/me", response_model=BillingStatus)
async def get_billing_me(
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> BillingStatus:
    async with SessionLocal() as session:
        return await billing_service.get_status(session, current_user.id)


@router.get("/packs", response_model=list[CreditPackRead])
async def list_credit_packs(
    _current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> list[CreditPackRead]:
    return [CreditPackRead(id=p.id, price_usd=p.price_usd, credits=p.credits) for p in CREDIT_PACKS]


@router.get("/plans", response_model=list[PlanRead])
async def list_plans(
    _current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> list[PlanRead]:
    """Purchasable subscription tiers — monthly price + the AI features each unlocks."""
    return billing_service.list_plans()


@router.post("/subscribe", response_model=BillingStatus)
async def subscribe(
    payload: SubscribeRequest,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> BillingStatus:
    """Stub: select a paid tier (no real charge yet)."""
    async with SessionLocal() as session:
        await billing_service.subscribe(session, current_user.id, payload.tier)
        await session.commit()
        return await billing_service.get_status(session, current_user.id)


@router.post("/checkout", response_model=BillingStatus)
async def checkout(
    payload: CheckoutRequest,
    current_user: Annotated[AuthUser, Depends(get_current_user)],
) -> BillingStatus:
    """Stub: 'buy' a credit pack — grants its credits with no real charge."""
    async with SessionLocal() as session:
        try:
            await billing_service.grant_pack(session, current_user.id, payload.pack_id)
        except UnknownPackError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        # SubscriptionRequiredError → 403 is handled centrally in app.main.
        await session.commit()
        return await billing_service.get_status(session, current_user.id)
