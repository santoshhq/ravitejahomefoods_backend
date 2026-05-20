from fastapi import Form, HTTPException
from pydantic import BaseModel, Field, EmailStr, AnyHttpUrl
from typing import List,Optional

class Reviews(BaseModel):
    product_id:str
    rating:int=Field(gt=0, le=5, description="Rating of Product")
    review_title:str
    review_content:str
    review_images_url:Optional[List[AnyHttpUrl]] = None
    display_name:str
    email_address:EmailStr
    mobile_number:str
    avg_rating:Optional[float]=Field(default=None, ge=0, le=5)
    is_active:bool=Field(default=True)

    @classmethod
    def as_form(
        cls,
        product_id: str = Form(...),
        rating: int = Form(...),
        review_title: str = Form(...),
        review_content: str = Form(...),
        display_name: str = Form(...),
        email_address: EmailStr = Form(...),
        mobile_number: str = Form(...),
        is_active: bool = Form(True),
    ):
        if rating <= 0 or rating > 5:
            raise HTTPException(status_code=400, detail="rating must be > 0 and <= 5")
        return cls(
            product_id=product_id,
            rating=rating,
            review_title=review_title,
            review_content=review_content,
            display_name=display_name,
            email_address=email_address,
            mobile_number=mobile_number,
            is_active=is_active,
        )


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, gt=0, le=5)
    review_title: Optional[str] = None
    review_content: Optional[str] = None
    display_name: Optional[str] = None
    email_address: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    is_active: Optional[bool] = None

    @classmethod
    def as_form(
        cls,
        rating: Optional[int] = Form(None),
        review_title: Optional[str] = Form(None),
        review_content: Optional[str] = Form(None),
        display_name: Optional[str] = Form(None),
        email_address: Optional[EmailStr] = Form(None),
        mobile_number: Optional[str] = Form(None),
        is_active: Optional[bool] = Form(None),
    ):
        if rating is not None and (rating <= 0 or rating > 5):
            raise HTTPException(status_code=400, detail="rating must be > 0 and <= 5")
        return cls(
            rating=rating,
            review_title=review_title,
            review_content=review_content,
            display_name=display_name,
            email_address=email_address,
            mobile_number=mobile_number,
            is_active=is_active,
        )