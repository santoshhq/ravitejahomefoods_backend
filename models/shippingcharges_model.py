from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


# ==========================================
# ZIPCODE ZONE
# ==========================================

class Zone(BaseModel):
    start_zipcode: int
    end_zipcode: int

    charge_per_kg: float

    free_delivery_min_order_value: float


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