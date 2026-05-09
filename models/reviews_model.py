from pydantic import BaseModel,Field,EmailStr,AnyHttpUrl
from typing import List,Optional

class Reviews(BaseModel):
    product_id:str
    rating:int=Field(gt=1,lt=5,description="Rating of Product")
    review_title:str
    review_content:str
    review_images_url:Optional[List[AnyHttpUrl]]
    display_name:str
    email_address:EmailStr
    mobile_number:str
    is_active:bool=Field(default=True)