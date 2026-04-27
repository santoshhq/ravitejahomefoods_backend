from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional


class UserModel(BaseModel):
    email: str
    is_verified: bool = True
    last_login: Optional[datetime] = None


class OTPModel(BaseModel):
    email: str
    otp: str
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(minutes=5)
    )
    attempts: int = 0