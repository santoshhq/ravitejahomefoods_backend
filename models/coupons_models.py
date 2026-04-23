from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime, timezone


# --- Shared cross-field validator (DRY) ---
def validate_percentage_fields(values: dict) -> dict:
    coupon_type = values.get("coupon_type")
    max_discount = values.get("maximum_discount")

    if coupon_type == "percentage":
        if max_discount is None:
            raise ValueError("maximum_discount is required when coupon_type is 'percentage'")

    return values


class CreateCoupon(BaseModel):
    couponcode: str = Field(..., description="Coupon code")
    coupon_type: Literal["percentage", "fixed"] = Field(..., description="Type of coupon")
    value: float = Field(..., gt=0, description="Discount amount or percentage value")
    maximum_discount: Optional[float] = Field(None, ge=0, description="Max discount (percentage type only)")
    minimum_bill: Optional[float] = Field(None, ge=0, description="Minimum order value to apply this coupon")
    is_active: bool = Field(default=True)
    expire_date: Optional[datetime] = Field(None, description="Coupon expiration date")
    admin_id: str = Field(..., description="Admin ID who created the coupon")

    @field_validator("value")
    @classmethod
    def validate_percentage_value(cls, v, info):
        if info.data.get("coupon_type") == "percentage" and v > 100:
            raise ValueError("Percentage value cannot exceed 100")
        return v

    @field_validator("expire_date", mode="before")
    @classmethod
    def validate_expire_date(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            try:
                v = datetime.fromisoformat(v)
            except ValueError:
                raise ValueError("Invalid datetime format. Use ISO 8601 format (e.g. 2025-12-31T00:00:00)")
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v < datetime.now(timezone.utc):
            raise ValueError("expire_date cannot be in the past")
        return v

    @model_validator(mode="before")
    @classmethod
    def validate_cross_fields(cls, values):
        return validate_percentage_fields(values)


class UpdateCoupon(BaseModel):
    couponcode: Optional[str] = Field(None, description="Coupon code")
    coupon_type: Optional[Literal["percentage", "fixed"]] = Field(None, description="Type of coupon")
    value: Optional[float] = Field(None, gt=0, description="Discount amount or percentage value")
    maximum_discount: Optional[float] = Field(None, ge=0, description="Max discount (percentage type only)")
    minimum_bill: Optional[float] = Field(None, ge=0, description="Minimum order value to apply this coupon")
    is_active: Optional[bool] = Field(None)
    expire_date: Optional[datetime] = Field(None, description="Coupon expiration date")

    @field_validator("value")
    @classmethod
    def validate_percentage_value(cls, v, info):
        if v is not None and info.data.get("coupon_type") == "percentage" and v > 100:
            raise ValueError("Percentage value cannot exceed 100")
        return v

    @field_validator("expire_date", mode="before")
    @classmethod
    def validate_expire_date(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            try:
                v = datetime.fromisoformat(v)
            except ValueError:
                raise ValueError("Invalid datetime format. Use ISO 8601 format (e.g. 2025-12-31T00:00:00)")
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v < datetime.now(timezone.utc):
            raise ValueError("expire_date cannot be in the past")
        return v

    @model_validator(mode="before")
    @classmethod
    def validate_cross_fields(cls, values):
        return validate_percentage_fields(values)