import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class RequestOtp(BaseModel):
    email: EmailStr


class VerifyOtp(BaseModel):
    email: EmailStr
    code: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestOtpResponse(BaseModel):
    message: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    created_at: datetime
