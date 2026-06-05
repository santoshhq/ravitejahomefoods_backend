from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal
from datetime import datetime
from models.cart_model import CartItem


class Address(BaseModel):
    name: str = Field(..., description="Full name of the recipient")
    mobile: str = Field(..., description="10-digit mobile number")
    address_line: str = Field(..., description="Full street address/house number")
    city: str
    state: str = Field(..., description="State of residence")
    country: str = Field(default="India")
    pincode: str = Field(..., description="6-digit pincode")


class PlaceOrderRequest(BaseModel):
    email: EmailStr  # Mandatory email for receipts
    shipping_address: Address
    billing_address: Optional[Address] = None  # If None, use shipping address
    coupon_code: Optional[str] = None
    guest_id: Optional[str] = None # Support for guest identification


class PaymentVerificationRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    guest_id: Optional[str] = None


class DeliveryEstimateRequest(BaseModel):
    country: str
    state: str
    pincode: str
    guest_id: Optional[str] = None


class OrderModel(BaseModel):
    user_email: Optional[EmailStr] = None
    guest_id: Optional[str] = None
    items: List[CartItem]
    shipping_address: Address
    billing_address: Address
    subtotal: float
    discount_amount: float = 0.0
    gst_amount: float = 0.0
    delivery_charges: float = 0.0
    grand_total: float
    coupon_code: Optional[str] = None
    
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    
    order_status: Literal["pending", "confirmed", "shipped", "delivered"] = "pending"
    payment_status: Literal["paid"] = "paid"
    
  
