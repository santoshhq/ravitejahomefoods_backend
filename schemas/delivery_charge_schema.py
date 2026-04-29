from pydantic import BaseModel, Field
from typing import Optional

class DeliveryChargeBase(BaseModel):
    country: str
    state: str
    start_zipcode: int
    end_zipcode: int
    charge_per_kg: float = Field(..., description="Delivery charge per kg in INR")
    free_delivery_min_order: Optional[float] = Field(None, description="Minimum order value for free delivery")

class DeliveryChargeCreate(DeliveryChargeBase):
    pass

class DeliveryChargeUpdate(DeliveryChargeBase):
    pass

class DeliveryChargeOut(DeliveryChargeBase):
    id: int

    class Config:
        orm_mode = True
