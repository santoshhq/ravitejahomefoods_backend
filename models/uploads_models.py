from pydantic import BaseModel,AnyHttpUrl
from typing import List
class UploadImageResponse(BaseModel):
    image_url=List[AnyHttpUrl]