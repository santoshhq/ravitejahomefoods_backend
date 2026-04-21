from pydantic import BaseModel, Field,  AnyHttpUrl, field_validator,HttpUrl
from typing import List, Optional, Literal, Union

class Pricing(BaseModel):
    weight: str = Field(..., description="Weight of the product variant")
    price: float = Field(..., gt=0, description="Price must be positive")
    stock: Optional[int] = Field(default=None, ge=0, description="Stock must be non-negative if provided")

    @field_validator("price")
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Price must be positive")
        return v

    @field_validator("stock")
    def stock_must_be_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("Stock must be non-negative")
        return v


class Products(BaseModel):
    product_name: str = Field(..., description="Name of the product")
    description: str = Field(..., description="Description of the product")
    images_url: List[AnyHttpUrl] = Field(..., description="S3 image URLs for the product")
    business_type: Literal["retail", "wholesale"] = Field(..., description="Business type")
    category_id: str = Field(..., description="Category ID as string")
    subcategory: Optional[str] = Field(default=None, description="Subcategory based on selected category")
    pricing: List[Pricing] = Field(..., description="List of pricing options")
    is_active: bool = Field(default=True)

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        # Convert AnyHttpUrl objects to plain strings for MongoDB
        data["images_url"] = [str(url) for url in data["images_url"]]
        return data

class UpdateProduct(BaseModel):
    product_name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    images_url: Optional[List[AnyHttpUrl]] = Field(default=None)
    business_type: Optional[Literal["retail", "wholesale"]] = Field(default=None)
    category_id: Optional[str] = Field(default=None)
    subcategory: Optional[str] = Field(default=None, description="Subcategory based on selected category")
    pricing: Optional[List[Pricing]] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        if data.get("images_url"):
            data["images_url"] = [str(url) for url in data["images_url"]]
        return data