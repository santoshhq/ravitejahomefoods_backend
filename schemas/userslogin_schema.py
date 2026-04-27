from pydantic import BaseModel, EmailStr

class OTPRequestSchema(BaseModel):
	email: EmailStr

class OTPVerifySchema(BaseModel):
	email: EmailStr
	otp: str

class TokenResponseSchema(BaseModel):
	access_token: str
	token_type: str
