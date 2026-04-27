from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CartItem(BaseModel):
    product_id: str = Field(..., description="Product ObjectId as string")
    product_name: str
    image_url: str
    weight: str                         # e.g. "500g", "1Kg"
    price: float = Field(..., gt=0)
    quantity: int = Field(..., ge=1)
    business_type: str                  # "retail" | "wholesale"


class BulkAddToCartRequest(BaseModel):
    items: List[CartItem] = Field(..., min_length=1, description="List of items to add")
    guest_id: Optional[str] = Field(
        default=None,
        description="Send this if the user is not logged in (UUID from localStorage)"
    )


class UpdateCartItemRequest(BaseModel):
    product_id: str
    weight: str
    quantity: int = Field(..., ge=0, description="Set to 0 to remove the item")
    guest_id: Optional[str] = None


class ApplyCouponRequest(BaseModel):
    coupon_code: str
    guest_id: Optional[str] = None


class RemoveCouponRequest(BaseModel):
    guest_id: Optional[str] = None


class MergeCartRequest(BaseModel):
    guest_id: str = Field(..., description="Guest UUID to merge into the logged-in user cart")
