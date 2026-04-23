from pydantic import BaseModel,Field
from typing import Optional,List,Literal

class SubCategory(BaseModel):
    name:str=Field(...,)


class CreateCategory(BaseModel):
    name:str=Field(...,)
    business_type: Literal["retail", "wholesale"] = Field(...,)
    subcategory: Optional[List[SubCategory]] = Field(default=None)
    admin_id: str = Field(..., description="Admin ID who created the category")


class UpdateCategory(BaseModel):
    name: Optional[str] = Field(default=None)
    business_type: Optional[Literal["retail", "wholesale"]] = Field(default=None)
    subcategory: Optional[List[SubCategory]] = Field(default=None)
    admin_id: Optional[str] = Field(default=None, description="Admin ID who created the category")