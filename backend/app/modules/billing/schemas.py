from pydantic import BaseModel

from app.modules.billing.config import PaidTier


class BillingStatus(BaseModel):
    tier: str
    credits: int
    access: dict[str, bool]  # feature -> unlocked by current tier
    costs: dict[str, int]  # feature -> credit cost


class CreditPackRead(BaseModel):
    id: str
    price_usd: int
    credits: int


class PlanRead(BaseModel):
    tier: str
    price_usd: int  # monthly subscription price
    features: list[str]  # feature ids this tier unlocks


class SubscribeRequest(BaseModel):
    tier: PaidTier  # can only subscribe to a paid tier


class CheckoutRequest(BaseModel):
    pack_id: str
