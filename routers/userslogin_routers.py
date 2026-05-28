from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import EmailStr
from datetime import datetime, timedelta
import random
import string
import os
import httpx
from config.collection import users_collection, orders_collection
from models.userslogin_models import OTPModel,UserModel
from config.jwt_auth.token_creation import create_access_token, decode_access_token
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from config.rate_limiter import limiter, RATE_LIMITS

userlogin_router = APIRouter(prefix="/user-login", tags=["User Login"])

# Helper to generate OTP
def generate_otp(length=6):
	return ''.join(random.choices(string.digits, k=length))

# Send OTP using Resend API
async def send_otp_email(email: str, otp: str):
	resend_api_key = os.getenv("RESEND_API_KEY")
	if not resend_api_key:
		raise RuntimeError("RESEND_API_KEY not set in environment")
	async with httpx.AsyncClient() as client:
		response = await client.post(
			"https://api.resend.com/emails",
			headers={
				"Authorization": f"Bearer {resend_api_key}",
				"Content-Type": "application/json",
			},
			json={
				"from": "noreply@genxtechnologies.tech",
				"to": [email],
				"subject": "Your OTP Code",
				   "html": f"""
					   <div style='font-family: Arial, sans-serif; max-width: 400px; margin: auto; border: 1px solid #e0e0e0; border-radius: 8px; box-shadow: 0 2px 8px #f0f0f0; padding: 24px; background: #fff;'>
						   <h2 style='color: #2d7ff9; text-align: center;'>RaviTeja Foods Login OTP</h2>
						   <p style='font-size: 16px; color: #333;'>
							   Hello,<br><br>
							   Your One-Time Password (OTP) for login is:
						   </p>
						   <div style='text-align: center; margin: 24px 0;'>
							   <span style='display: inline-block; font-size: 28px; letter-spacing: 8px; color: #2d7ff9; font-weight: bold; background: #f4f8ff; padding: 12px 24px; border-radius: 6px; border: 1px dashed #2d7ff9;'>
								   {otp}
							   </span>
						   </div>
						   <p style='font-size: 14px; color: #666;'>
							   This OTP is valid for 5 minutes. Please do not share it with anyone.<br><br>
							   If you did not request this, you can safely ignore this email.
						   </p>
						   <p style='font-size: 13px; color: #aaa; text-align: center; margin-top: 32px;'>
							   &copy; {datetime.now().year} RaviTeja Foods
						   </p>
					   </div>
				   """
			},
			timeout=10.0
		)
		if response.status_code not in (200, 202):
			raise HTTPException(status_code=500, detail="Failed to send OTP email")

# Endpoint: Request OTP
@userlogin_router.post("/request-otp")
@limiter.limit(RATE_LIMITS["user_request_otp"])
async def request_otp(request: Request, email: EmailStr):
	otp = generate_otp()
	expires_at = datetime.utcnow() + timedelta(minutes=5)
	await users_collection.update_one(
		{"email": email},
		{"$set": {"otp": otp, "otp_expires_at": expires_at, "otp_attempts": 0}},
		upsert=True
	)
	await send_otp_email(email, otp)
	return {"message": "OTP sent to email"}

# Endpoint: Verify OTP and login
@userlogin_router.post("/verify-otp")
@limiter.limit(RATE_LIMITS["user_verify_otp"])
async def verify_otp(request: Request, email: EmailStr, otp: str):
	user = await users_collection.find_one({"email": email})
	if not user or "otp" not in user:
		raise HTTPException(status_code=400, detail="OTP not requested or user not found")
	if user["otp"] != otp:
		await users_collection.update_one({"email": email}, {"$inc": {"otp_attempts": 1}})
		raise HTTPException(status_code=401, detail="Invalid OTP")
	if datetime.utcnow() > user["otp_expires_at"]:
		raise HTTPException(status_code=401, detail="OTP expired")
	# OTP valid, clear OTP and issue JWT
	await users_collection.update_one(
		{"email": email},
		{"$set": {"is_verified": True, "last_login": datetime.utcnow()}, "$unset": {"otp": "", "otp_expires_at": "", "otp_attempts": ""}}
	)
	token = create_access_token({"email": email})
	return {"access_token": token, "token_type": "bearer"}

# Example protected route


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user-login/verify-otp")

def get_current_user(token: str = Depends(oauth2_scheme)):
	try:
		payload = decode_access_token(token)
		email = payload.get("email")
		if not email:
			raise HTTPException(status_code=401, detail="Invalid token")
		return email
	except JWTError:
		raise HTTPException(status_code=401, detail="Invalid token")

@userlogin_router.get("/me")
@limiter.limit(RATE_LIMITS["user_me"])
async def get_me(request: Request, email: str = Depends(get_current_user)):
	user = await users_collection.find_one({"email": email})
	if not user:
		raise HTTPException(status_code=404, detail="User not found")
	user["id"] = str(user.pop("_id"))
	return user


###################################################
# GET USER ORDERS
###################################################

@userlogin_router.get("/orders")
@limiter.limit(RATE_LIMITS["user_me"])
async def get_user_orders(request: Request, email: str = Depends(get_current_user)):
	"""
	Fetch all orders for the authenticated user by their email
	
	Returns:
	- List of orders with order details, status, and payment information
	"""
	orders = await orders_collection.find(
		{"user_email": email}
	).sort("_id", -1).to_list(None)
	
	if not orders:
		return {
			"email": email,
			"orders": [],
			"total_orders": 0,
			"message": "No orders found"
		}
	
	# Serialize orders
	serialized_orders = []
	for order in orders:
		order_data = {
			"order_id": str(order.get("_id")),
			"user_email": order.get("user_email"),
			"guest_id": order.get("guest_id"),
			"items": order.get("items", []),
			"shipping_address": order.get("shipping_address"),
			"billing_address": order.get("billing_address"),
			"subtotal": order.get("subtotal"),
			"discount_amount": order.get("discount_amount", 0.0),
			"gst_amount": order.get("gst_amount", 0.0),
			"delivery_charges": order.get("delivery_charges", 0.0),
			"grand_total": order.get("grand_total"),
			"coupon_code": order.get("coupon_code"),
			"razorpay_order_id": order.get("razorpay_order_id"),
			"razorpay_payment_id": order.get("razorpay_payment_id"),
			"order_status": order.get("order_status"),
			"payment_status": order.get("payment_status"),
			"created_at": order.get("created_at"),
			"updated_at": order.get("updated_at")
		}
		serialized_orders.append(order_data)
	
	return {
		"email": email,
		"orders": serialized_orders,
		"total_orders": len(serialized_orders)
	}
