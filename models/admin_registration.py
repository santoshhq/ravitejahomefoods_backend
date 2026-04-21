from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class Registration(BaseModel):
    fullname: str = Field(...)
    mobile: str = Field(..., min_length=10, max_length=10)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8)
    
class updateRegistration(BaseModel):
    fullname: Optional[str] = None
    mobile: Optional[str] = Field(default=None, min_length=10, max_length=10)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=8)


class AdminPublic(BaseModel):
    id: str
    fullname: str
    email: EmailStr
    mobile: str


class RegistrationResponse(BaseModel):
    message: str
    data: AdminPublic


class LoginResponse(BaseModel):
    message: str
    access_token: str
    token_type: str
    admin: AdminPublic