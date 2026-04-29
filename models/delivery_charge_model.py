from sqlalchemy import Column, Integer, String, Float
from config.db import Base

class DeliveryCharge(Base):
    __tablename__ = "delivery_charges"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String, nullable=False)
    state = Column(String, nullable=False)
    start_zipcode = Column(Integer, nullable=False)
    end_zipcode = Column(Integer, nullable=False)
    charge_per_kg = Column(Float, nullable=False)
    free_delivery_min_order = Column(Float, nullable=True)
