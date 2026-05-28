from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ==========================================
# ZIPCODE ZONE
# ==========================================

class Zone(BaseModel):
    start_zipcode: int
    end_zipcode: int

    charge_per_kg: float

    free_delivery_min_order_value: Optional[float] = None


# ==========================================
# STATE SHIPPING
# ==========================================

class StateShipping(BaseModel):
    state_name: str
    zones: List[Zone]


# ==========================================
# COUNTRY CONFIG CREATE
# ==========================================

class CountryShippingCreate(
    BaseModel
):
    country: str
    states: List[StateShipping]


# ==========================================
# ADD STATE
# ==========================================

class AddStateRequest(
    BaseModel
):
    country: str
    state: StateShipping


# ==========================================
# ADD ZONE
# ==========================================

class AddZoneRequest(
    BaseModel
):
    country: str

    state_name: str

    zone: Zone


# ==========================================
# UPDATE ZONE
# ==========================================

class UpdateZoneRequest(
    BaseModel
):
    """
    Request model for updating/editing an existing zone
    All fields except country, state_name, and old zipcode ranges are optional
    Admin can update any combination of fields
    """
    country: str = Field(..., description="Country name")
    state_name: str = Field(..., description="State name")
    old_start_zipcode: int = Field(..., description="Current start zipcode to identify zone")
    old_end_zipcode: int = Field(..., description="Current end zipcode to identify zone")
    new_charge_per_kg: Optional[float] = Field(None, description="Updated charge per kg (optional)")
    new_free_delivery_min_order_value: Optional[float] = Field(None, description="Updated free delivery threshold (optional)")


# ==========================================
# DELETE ZONE REQUEST
# ==========================================

class DeleteZoneRequest(
    BaseModel
):
    """
    Request model for deleting a zone
    """
    country: str = Field(..., description="Country name")
    state_name: str = Field(..., description="State name")
    start_zipcode: int = Field(..., description="Zone start zipcode")
    end_zipcode: int = Field(..., description="Zone end zipcode")


# ==========================================
# DELETE STATE REQUEST
# ==========================================

class DeleteStateRequest(
    BaseModel
):
    """
    Request model for deleting a complete state
    """
    country: str = Field(..., description="Country name")
    state_name: str = Field(..., description="State name to delete")


# ==========================================
# DELETE COUNTRY REQUEST
# ==========================================

class DeleteCountryRequest(
    BaseModel
):
    """
    Request model for deleting a complete country and all its states/zones
    """
    country: str = Field(..., description="Country name to delete")


# ==========================================
# SHIPPING ESTIMATE
# ==========================================

class ShippingEstimateRequest(
 BaseModel
):
  

    country:str
    state:str
    zipcode:int

    cart_weight_grams:float

    order_total:float