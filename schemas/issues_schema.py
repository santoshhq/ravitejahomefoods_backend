from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Optional, Literal


class IssuesCreate(BaseModel):
    order_id: str = Field(..., min_length=1)
    payment_id: str = Field(..., min_length=1)
    email: EmailStr = Field(...)
    mobile: str = Field(..., min_length=10)
    issue_type: Literal["Refund/Return", "Cancel Order", "Replace Order"]
    detailed_reason: str = Field(..., min_length=10)
    images: Optional[List[str]] = None

    @field_validator("images")
    @classmethod
    def validate_images(cls, v, info):
        """
        Validate images based on issue_type:
        - Required for "Refund/Return" and "Replace Order"
        - Optional for "Cancel Order"
        """
        issue_type = info.data.get("issue_type")
        
        if issue_type in ["Refund/Return", "Replace Order"]:
            if not v or len(v) == 0:
                raise ValueError(
                    f"Images are required for '{issue_type}'. Please upload at least one image."
                )
        
        return v


class IssuesResponse(BaseModel):
    issue_id: str
    order_id: str
    email: EmailStr
    issue_type: Literal["Refund/Return", "Cancel Order", "Replace Order"]
    detailed_reason: str
    image_urls: Optional[List[str]] = None
    status: Literal["Pending", "Solved"] = "Pending"

    class Config:
        from_attributes = True
