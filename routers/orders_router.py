import os
from bson import ObjectId
import razorpay
import httpx
from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.encoders import jsonable_encoder
import random
import string
from datetime import datetime, timezone, timedelta

# Indian Standard Time (UTC+5:30)
_IST = timezone(timedelta(hours=5, minutes=30))
def now_ist() -> str:
    """Return current IST datetime as a readable string: 05 Jun 2026, 10:09 AM"""
    return datetime.now(_IST).strftime("%d %b %Y, %I:%M %p")
from typing import Optional
from math import ceil
import re
import json
from config.collection import (
    orders_collection,
    carts_collection,
    users_collection,
    products_collection,
    shipping_charges,
)
from models.order_model import (
    PlaceOrderRequest,
    PaymentVerificationRequest,
    DeliveryEstimateRequest,
    OrderModel,
)
from schemas.order_schema import order_data, all_orders_data, single_order_data
from schemas.cart_schema import cart_data
from routers.cart_router import get_current_user, get_optional_user
from config.jwt_auth.token_creation import get_current_admin
from config.rate_limiter import limiter, RATE_LIMITS
from config.redis_caching import redis_client, clear_orders_routers_cache, CACHE_TTL_SECONDS
orders_router = APIRouter(prefix="/orders", tags=["Orders"])

# Initialize Razorpay Client
razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)

def generate_custom_order_id():
    year = datetime.now().year
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
    return f"ORD{year}{random_part}"

# Send Confirmation Email using Resend
async def send_order_confirmation_email(user_email: str, order: dict):
    resend_api_key = os.getenv("RESEND_API_KEY")
    if not resend_api_key:
        return # Fallback if email service is down
    
    items_html = ""
    for item in order["items"]:
        items_html += f"""
        <tr>
            <td style='padding: 12px 16px; border-bottom: 1px solid #e8dcc8; font-size: 14px; color: #3d2c1e;'>
                <strong>{item['product_name']}</strong>
                <span style='display: block; font-size: 12px; color: #8a7060; margin-top: 2px;'>{item['weight']}</span>
            </td>
            <td style='padding: 12px 16px; border-bottom: 1px solid #e8dcc8; font-size: 14px; color: #3d2c1e; text-align: center;'>{item['quantity']}</td>
            <td style='padding: 12px 16px; border-bottom: 1px solid #e8dcc8; font-size: 14px; color: #3d2c1e; text-align: center;'>₹{item['price']}</td>
            <td style='padding: 12px 16px; border-bottom: 1px solid #e8dcc8; font-size: 14px; color: #7B1113; font-weight: 700; text-align: right;'>₹{item['price'] * item['quantity']}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Order Confirmed - RaviTeja Home Foods</title>
    </head>
    <body style='margin: 0; padding: 0; background-color: #f5f0e8; font-family: Georgia, "Times New Roman", serif;'>

        <!-- Outer wrapper -->
        <table width="100%" cellpadding="0" cellspacing="0" style='background-color: #f5f0e8; padding: 32px 16px;'>
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style='max-width: 600px; width: 100%;'>

                        <!-- ===== HEADER ===== -->
                        <tr>
                            <td style='background: linear-gradient(135deg, #7B1113 0%, #5A0D0F 100%); border-radius: 16px 16px 0 0; padding: 36px 40px; text-align: center;'>
                                <!-- Logo / Brand Name -->
                                <div style='display: inline-block; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 50px; padding: 6px 20px; margin-bottom: 16px;'>
                                    <span style='color: #c9a84c; font-size: 11px; letter-spacing: 3px; text-transform: uppercase; font-family: Arial, sans-serif;'>Home Foods</span>
                                </div>
                                <h1 style='margin: 0 0 4px 0; font-size: 30px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;'>RaviTeja Home Foods Pvt Ltd</h1>
                                <p style='margin: 0; font-size: 13px; color: #E8D7D7; letter-spacing: 1px; font-family: Arial, sans-serif; text-transform: uppercase;'>Pure · Natural · Homemade</p>

                                <!-- Success Badge -->
                                <div style='margin-top: 28px; background: rgba(201, 168, 76, 0.15); border: 1.5px solid #c9a84c; border-radius: 50px; display: inline-block; padding: 10px 28px;'>
                                    <span style='color: #c9a84c; font-size: 15px; font-weight: 600; font-family: Arial, sans-serif;'>✓ &nbsp;Order Confirmed!</span>
                                </div>
                            </td>
                        </tr>

                        <!-- ===== GREETING BAND ===== -->
                        <tr>
                            <td style='background-color: #c9a84c; padding: 14px 40px;'>
                                <p style='margin: 0; font-size: 13px; color: #5A0D0F; font-family: Arial, sans-serif; font-weight: 600; text-align: center; letter-spacing: 0.5px;'>
                                    🙏 &nbsp;Thank you for trusting our homemade goodness!
                                </p>
                            </td>
                        </tr>

                        <!-- ===== MAIN BODY ===== -->
                        <tr>
                            <td style='background-color: #ffffff; padding: 36px 40px;'>

                                <p style='margin: 0 0 8px 0; font-size: 16px; color: #3d2c1e;'>Dear Customer,</p>
                                <p style='margin: 0 0 28px 0; font-size: 15px; color: #5a4535; line-height: 1.7;'>
                                    Your order has been successfully placed and payment confirmed. We're already preparing your fresh homemade products with love and care. 🌿
                                </p>

                                <!-- Order Meta Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style='background: #f9f5ee; border: 1px solid #e8dcc8; border-radius: 10px; margin-bottom: 28px;'>
                                    <tr>
                                        <td style='padding: 16px 20px; border-right: 1px solid #e8dcc8;'>
                                            <p style='margin: 0; font-size: 11px; color: #8a7060; text-transform: uppercase; letter-spacing: 1px; font-family: Arial, sans-serif;'>Order ID</p>
                                            <p style='margin: 4px 0 0 0; font-size: 14px; color: #7B1113; font-weight: 700; font-family: Arial, sans-serif;'>{order.get('custom_order_id', order['razorpay_order_id'])}</p>
                                        </td>
                                        <td style='padding: 16px 20px;'>
                                            <p style='margin: 0; font-size: 11px; color: #8a7060; text-transform: uppercase; letter-spacing: 1px; font-family: Arial, sans-serif;'>Payment ID</p>
                                            <p style='margin: 4px 0 0 0; font-size: 14px; color: #7B1113; font-weight: 700; font-family: Arial, sans-serif;'>{order.get('razorpay_payment_id', 'N/A')}</p>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Section Title -->
                                <h3 style='margin: 0 0 12px 0; font-size: 13px; color: #8a7060; text-transform: uppercase; letter-spacing: 2px; font-family: Arial, sans-serif; font-weight: 600; border-bottom: 2px solid #c9a84c; padding-bottom: 8px;'>
                                    🛒 &nbsp;Order Summary
                                </h3>

                                <!-- Items Table -->
                                <table width="100%" cellpadding="0" cellspacing="0" style='border: 1px solid #e8dcc8; border-radius: 10px; overflow: hidden; margin-bottom: 20px;'>
                                    <thead>
                                        <tr style='background: #7B1113;'>
                                            <th style='text-align: left; padding: 12px 16px; font-size: 11px; color: #E8D7D7; text-transform: uppercase; letter-spacing: 1.5px; font-family: Arial, sans-serif; font-weight: 600;'>Item</th>
                                            <th style='text-align: center; padding: 12px 16px; font-size: 11px; color: #E8D7D7; text-transform: uppercase; letter-spacing: 1.5px; font-family: Arial, sans-serif; font-weight: 600;'>Qty</th>
                                            <th style='text-align: center; padding: 12px 16px; font-size: 11px; color: #E8D7D7; text-transform: uppercase; letter-spacing: 1.5px; font-family: Arial, sans-serif; font-weight: 600;'>Price</th>
                                            <th style='text-align: right; padding: 12px 16px; font-size: 11px; color: #E8D7D7; text-transform: uppercase; letter-spacing: 1.5px; font-family: Arial, sans-serif; font-weight: 600;'>Total</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {items_html}
                                    </tbody>
                                </table>

                                <!-- Pricing Breakdown -->
                                <table width="100%" cellpadding="0" cellspacing="0" style='margin-bottom: 28px;'>
                                    <tr>
                                        <td style='padding: 5px 0; font-size: 14px; color: #5a4535; font-family: Arial, sans-serif;'>Subtotal</td>
                                        <td style='padding: 5px 0; font-size: 14px; color: #3d2c1e; text-align: right; font-family: Arial, sans-serif;'>₹{order['subtotal']}</td>
                                    </tr>
                                    <tr>
                                        <td style='padding: 5px 0; font-size: 14px; color: #5a4535; font-family: Arial, sans-serif;'>
                                            Discount
                                            {'<span style="background:#F8F1E7; color:#7B1113; font-size:11px; padding:2px 8px; border-radius:4px; margin-left:8px; font-weight:600;">' + order.get('coupon_code', '') + '</span>' if order.get('coupon_code') else ''}
                                        </td>
                                        <td style='padding: 5px 0; font-size: 14px; color: #7B1113; font-weight: 600; text-align: right; font-family: Arial, sans-serif;'>-₹{order['discount_amount']}</td>
                                    </tr>
                                    <tr>
                                        <td style='padding: 5px 0; font-size: 14px; color: #5a4535; font-family: Arial, sans-serif;'>GST</td>
                                        <td style='padding: 5px 0; font-size: 14px; color: #5a4535; text-align: right; font-family: Arial, sans-serif; font-style: italic;'>Included</td>
                                    </tr>
                                    <tr>
                                        <td style='padding: 5px 0 12px 0; font-size: 14px; color: #5a4535; font-family: Arial, sans-serif; border-bottom: 1px dashed #e8dcc8;'>Delivery</td>
                                        <td style='padding: 5px 0 12px 0; font-size: 14px; color: #3d2c1e; text-align: right; font-family: Arial, sans-serif; border-bottom: 1px dashed #e8dcc8;'>₹{order['delivery_charges']}</td>
                                    </tr>
                                    <tr>
                                        <td style='padding: 14px 20px; background: linear-gradient(135deg, #7B1113, #5A0D0F); border-radius: 10px 0 0 10px;'>
                                            <span style='font-size: 16px; color: #ffffff; font-family: Arial, sans-serif; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;'>Grand Total</span>
                                        </td>
                                        <td style='padding: 14px 20px; background: #c9a84c; border-radius: 0 10px 10px 0; text-align: right;'>
                                            <span style='font-size: 22px; color: #5A0D0F; font-family: Arial, sans-serif; font-weight: 800;'>₹{order['grand_total']}</span>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Delivery Address -->
                                <h3 style='margin: 0 0 12px 0; font-size: 13px; color: #8a7060; text-transform: uppercase; letter-spacing: 2px; font-family: Arial, sans-serif; font-weight: 600; border-bottom: 2px solid #c9a84c; padding-bottom: 8px;'>
                                    📦 &nbsp;Delivery Address
                                </h3>
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style='background: #f9f5ee; border: 1px solid #e8dcc8; border-left: 4px solid #7B1113; border-radius: 0 8px 8px 0; padding: 16px 20px;'>
                                            <p style='margin: 0; font-size: 15px; color: #3d2c1e; font-weight: 700; font-family: Arial, sans-serif;'>{order['shipping_address']['name']}</p>
                                            <p style='margin: 4px 0 0 0; font-size: 14px; color: #5a4535; font-family: Arial, sans-serif; line-height: 1.7;'>
                                                📱 {order['shipping_address']['mobile']}<br/>
                                                {order['shipping_address']['address_line']}, {order['shipping_address']['city']}<br/>
                                                {order['shipping_address'].get('state', '')}, {order['shipping_address']['country']} – {order['shipping_address']['pincode']}
                                            </p>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Reassurance Note -->
                                <table width="100%" cellpadding="0" cellspacing="0" style='margin-top: 28px;'>
                                    <tr>
                                        <td style='background: #F8F1E7; border-radius: 10px; padding: 16px 20px; text-align: center;'>
                                            <p style='margin: 0; font-size: 13px; color: #7B1113; font-family: Arial, sans-serif; line-height: 1.6;'>
                                                🌿 &nbsp;Your order will be freshly prepared and dispatched soon.<br/>
                                                For queries, reach us at <a href='mailto:support@ravitejahomefoods.in' style='color: #7B1113; font-weight: 700;'>support@ravitejahomefoods.in</a>
                                            </p>
                                        </td>
                                    </tr>
                                </table>

                            </td>
                        </tr>

                        <!-- ===== FOOTER ===== -->
                        <tr>
                            <td style='background: #5A0D0F; border-radius: 0 0 16px 16px; padding: 24px 40px; text-align: center;'>
                                <p style='margin: 0 0 8px 0; font-size: 15px; color: #c9a84c; font-weight: 700; letter-spacing: 1px; font-family: Arial, sans-serif;'>RaviTeja Home Foods</p>
                                <p style='margin: 0 0 12px 0; font-size: 12px; color: #D2A355; font-family: Arial, sans-serif;'>
                                    <a href='https://ravitejahomefoods.in' style='color: #D2A355; text-decoration: none;'>ravitejahomefoods.in</a>
                                </p>
                                <p style='margin: 0; font-size: 11px; color: #B88A3F; font-family: Arial, sans-serif;'>
                                    © {datetime.now().year} RaviTeja Home Foods. All rights reserved.
                                </p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>

    </body>
    </html>
    """

    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": "RaviTeja Home Foods <orders@ravitejahomefoods.in>",
                "to": [user_email],
                "subject": f"✅ Order Confirmed – {order.get('custom_order_id', order['razorpay_order_id'])} | RaviTeja Home Foods",
                "html": html_content
            },
            timeout=10.0
        )

# ── Internal helpers ─────────────────────────────────────────────────────────

def resolve_order_query(user_email: Optional[str], guest_id: Optional[str]) -> dict:
    if user_email:
        return {"user_email": user_email}
    if guest_id:
        return {"guest_id": guest_id}
    raise HTTPException(status_code=400, detail="User identification missing (email or guest_id)")


def parse_weight_grams(weight_value: Optional[str]) -> float:
    if not weight_value:
        return 0.0
    normalized = weight_value.strip().lower().replace(" ", "")
    match = re.match(r"([0-9]*\.?[0-9]+)(kg|g)$", normalized)
    if not match:
        return 0.0
    amount = float(match.group(1))
    unit = match.group(2)
    return amount * 1000 if unit == "kg" else amount


def calculate_cart_weight_grams(items: list[dict]) -> float:
    total = 0.0
    for item in items:
        grams = parse_weight_grams(item.get("weight"))
        qty = item.get("quantity", 0)
        total += grams * qty
    return total


async def estimate_delivery_cost(country: str, state: str, pincode: str, order_total: float, items: list[dict]) -> dict:
    try:
        zipcode = int(pincode)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid pincode")

    doc = await shipping_charges.find_one({"country": country})
    if not doc:
        raise HTTPException(status_code=404, detail="Shipping config not found")

    matched_zone = None
    for state_entry in doc.get("states", []):
        if state_entry.get("state_name", "").lower() == state.lower():
            for zone in state_entry.get("zones", []):
                if zone.get("start_zipcode") <= zipcode <= zone.get("end_zipcode"):
                    matched_zone = zone
                    break
        if matched_zone:
            break

    if not matched_zone:
        raise HTTPException(status_code=404, detail="No delivery available")

    free_min = matched_zone.get("free_delivery_min_order_value", 0)
    if order_total >= free_min:
        return {
            "country": country,
            "state": state,
            "pincode": pincode,
            "order_total": order_total,
            "shipping_charge": 0.0,
            "free_delivery": True,
            "message": "Free delivery applied",
        }

    weight_grams = calculate_cart_weight_grams(items)
    weight_kg = weight_grams / 1000 if weight_grams else 0.0
    billable_weight = ceil(weight_kg)
    shipping_charge = round(billable_weight * matched_zone.get("charge_per_kg", 0), 2)

    return {
        "country": country,
        "state": state,
        "pincode": pincode,
        "order_total": order_total,
        "actual_weight_kg": weight_kg,
        "billable_weight_kg": billable_weight,
        "charge_per_kg": matched_zone.get("charge_per_kg"),
        "shipping_charge": shipping_charge,
        "free_delivery": False,
    }


@orders_router.post("/delivery-estimate")
@limiter.limit(RATE_LIMITS["order_estimate"])
async def delivery_estimate(
    request: Request,
    req: DeliveryEstimateRequest,
    current_user: str = Depends(get_optional_user),
):
    query = resolve_order_query(current_user, req.guest_id)
    cart_doc = await carts_collection.find_one(query)
    if not cart_doc or not cart_doc.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")

    cart = cart_data(cart_doc)
    order_total = max(0.0, cart.get("total_preview", 0.0))
    return await estimate_delivery_cost(
        req.country,
        req.state,
        req.pincode,
        order_total,
        cart_doc.get("items", []),
    )


# Step 1: Place order now only creates Razorpay order and returns details, does NOT insert order into DB
@orders_router.post("/place", status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["order_place"])
async def place_order(request: Request, req: PlaceOrderRequest, current_user: str = Depends(get_optional_user)):
    query = resolve_order_query(current_user, req.guest_id)
    cart_doc = await carts_collection.find_one(query)
    if not cart_doc or not cart_doc.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")
    cart = cart_data(cart_doc)
    
    # Check pincode availability for retail products
    has_retail = any(item.get("business_type") == "retail" for item in cart["items"])
    if has_retail:
        pincode = req.shipping_address.pincode
        try:
            pincode_int = int(pincode)
            if not (500001 <= pincode_int <= 500115):
                raise ValueError()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Delivery for retail products is only available in Hyderabad "
            )
            
    subtotal = cart["subtotal"]
    discount = cart["discount_amount"]
    gst_rate = 0.0
    taxable_amount = max(0, subtotal - discount)
    gst_amount = 0.0
    delivery_preview = await estimate_delivery_cost(
        req.shipping_address.country,
        req.shipping_address.state,
        req.shipping_address.pincode,
        taxable_amount,
        cart_doc.get("items", []),
    )
    delivery_charges = delivery_preview.get("shipping_charge", 0.0)
    grand_total = round(taxable_amount + gst_amount + delivery_charges, 2)
    try:
        razorpay_order = razorpay_client.order.create({
            "amount": int(grand_total * 100),
            "currency": "INR",
            "payment_capture": "1"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Razorpay Error: {str(e)}")
        
    # Save the address info to the cart so we have it for verify-payment
    await carts_collection.update_one(
        query,
        {
            "$set": {
                "shipping_address": req.shipping_address.model_dump(),
                "billing_address": req.billing_address.model_dump() if req.billing_address else req.shipping_address.model_dump(),
                "order_contact_email": current_user if current_user else req.email
            }
        }
    )
    
    # Only return order details, do not insert into DB yet
    # Use the serialized cart (from cart_data) to avoid ObjectId serialization issues
    return {
        "status": "success",
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key": os.getenv("RAZORPAY_KEY_ID"),
        "grand_total": grand_total,
        "delivery_charges": delivery_charges,
        "cart": cart,
        "shipping_address": req.shipping_address.model_dump(),
        "billing_address": req.billing_address.model_dump() if req.billing_address else req.shipping_address.model_dump(),
        "email": current_user if current_user else req.email
    }



# Step 2: Insert order into DB only after payment is verified
@orders_router.post("/verify-payment")
@limiter.limit(RATE_LIMITS["order_verify"])
async def verify_payment(request: Request, req: PaymentVerificationRequest, current_user: str = Depends(get_optional_user)):
    # 1. Verify Signature
    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': req.razorpay_order_id,
            'razorpay_payment_id': req.razorpay_payment_id,
            'razorpay_signature': req.razorpay_signature
        })
    except Exception as e:
        print(f"Signature Verification Failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # 2. Fetch Cart and Details (simulate what was in /place)
    cart_query = resolve_order_query(current_user, req.guest_id if hasattr(req, 'guest_id') else None)
    cart_doc = await carts_collection.find_one(cart_query)
    if not cart_doc or not cart_doc.get("items"):
        print(f"Cart empty or not found for query: {cart_query}")
        raise HTTPException(status_code=400, detail="Cart is empty or not found for payment verification")

    # Check stock and status for each product before placing order
    unavailable_products = []
    for item in cart_doc["items"]:
        try:
            pid = ObjectId(item["product_id"]) if isinstance(item["product_id"], str) else item["product_id"]
        except Exception:
            pid = item["product_id"]
            
        product = await products_collection.find_one({
            "_id": pid
        })
        if not product or product.get("is_active") is False:
            unavailable_products.append({
                "product_id": str(item["product_id"]),
                "product_name": item.get("product_name"),
                "reason": "Product is inactive or deleted"
            })
    if unavailable_products:
        raise HTTPException(status_code=400, detail={"message": "Some products are unavailable", "products": unavailable_products})

    # All products available, proceed
    cart = cart_data(cart_doc)
    subtotal = cart["subtotal"]
    discount = cart["discount_amount"]
    gst_rate = 0.0
    taxable_amount = max(0, subtotal - discount)
    gst_amount = 0.0
    shipping_address = cart_doc.get("shipping_address") or {}
    delivery_preview = await estimate_delivery_cost(
        shipping_address.get("country", ""),
        shipping_address.get("state", ""),
        shipping_address.get("pincode", ""),
        taxable_amount,
        cart_doc.get("items", []),
    )
    delivery_charges = delivery_preview.get("shipping_charge", 0.0)
    grand_total = round(taxable_amount + gst_amount + delivery_charges, 2)
    custom_order_id = generate_custom_order_id()
    order_contact_email = cart_doc.get("order_contact_email", cart_doc.get("user_email"))
    order_doc = {
        "user_email": order_contact_email,
        "guest_id": cart_doc.get("guest_id"),
        "items": cart["items"],
        "shipping_address": cart_doc.get("shipping_address"),
        "billing_address": cart_doc.get("billing_address", cart_doc.get("shipping_address")),
        "subtotal": subtotal,
        "coupon_code": cart_doc.get("coupon_code"),
        "discount_amount": discount,
        "gst_amount": gst_amount,
        "delivery_charges": delivery_charges,
        "grand_total": grand_total,
        "razorpay_order_id": req.razorpay_order_id,
        "razorpay_payment_id": req.razorpay_payment_id,
        "custom_order_id": custom_order_id,
        "order_status": "pending",
        "payment_status": "paid",
        "created_at": now_ist(),
        "updated_at": now_ist()
    }
    result = await orders_collection.insert_one(order_doc)

    # 3. IDENTIFY Cart to clear
    if cart_doc.get("user_email"):
        await carts_collection.delete_one({"user_email": cart_doc["user_email"]})
    elif cart_doc.get("guest_id"):
        await carts_collection.delete_one({"guest_id": cart_doc["guest_id"]})

    # 4. Email Confirmation
    email_dest = order_contact_email
    if email_dest:
        await send_order_confirmation_email(email_dest, order_doc)
    await clear_orders_routers_cache()
    return {"status": "success", "message": "Order confirmed and cart cleared", "order_id": str(result.inserted_id), "custom_order_id": custom_order_id}


@orders_router.get("/guest/{guest_id}")
@limiter.limit(RATE_LIMITS["order_read"])
async def get_guest_orders(request: Request, guest_id: str):
    orders = await orders_collection.find({"guest_id": guest_id}).sort("created_at", -1).to_list(length=100)
    return {"data": all_orders_data(orders)}

# ── Admin Endpoints ──────────────────────────────────────────────────────────

@orders_router.get("/admin/all-orders")
async def get_all_orders_for_admin(
    adminid: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
    admin: dict = Depends(get_current_admin)
):

    cache_key = f"orders:admin:all:{skip}:{limit}"

    # Redis cache lookup
    try:
        cache_data = await redis_client.get(cache_key)

        if cache_data:
            return json.loads(cache_data)

    except Exception:
        pass

    # MongoDB query
    orders = (
        await orders_collection.find()
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(length=limit)
    )

    total_orders = await orders_collection.count_documents({})

    response = {
        "message": "All orders fetched successfully",
        "count": total_orders,
        "skip": skip,
        "limit": limit,
        "data": all_orders_data(orders)
    }

    encoded_response = jsonable_encoder(response)

    # Store in Redis
    try:
        await redis_client.set(
            cache_key,
            json.dumps(encoded_response),
            ex=CACHE_TTL_SECONDS,
        )

    except Exception:
        pass

    return response


@orders_router.patch("/admin/update-status/{order_id}")
@limiter.limit(RATE_LIMITS["order_verify"])
async def admin_update_order_status(
    request: Request,
    order_id: str,
    new_status: str,
    admin: dict = Depends(get_current_admin)
):
    """
    Admin endpoint to update order status.

    Parameters:
    - order_id: MongoDB ObjectId or custom_order_id
    - new_status: Target status to transition to

    Valid Status Transitions:
    - pending   → confirmed  (Admin accepts the order)
    - confirmed → shipped    (Admin marks order as shipped)
    - shipped   → delivered  (Admin marks order as delivered)

    Returns:
    - Updated order confirmation with previous and new status
    """

    # Allowed transitions: current_status → allowed next statuses
    VALID_TRANSITIONS: dict[str, list[str]] = {
        "pending":   ["confirmed"],
        "confirmed": ["shipped"],
        "shipped":   ["delivered"],
        "delivered": [],   # terminal state
    }

    # Human-friendly messages per transition
    TRANSITION_MESSAGES: dict[str, str] = {
        "confirmed": "Order confirmed successfully.",
        "shipped":   "Order marked as shipped.",
        "delivered": "Order marked as delivered.",
    }

    new_status = new_status.lower().strip()

    # Validate the requested status is a known value
    all_valid = {s for transitions in VALID_TRANSITIONS.values() for s in transitions}
    if new_status not in all_valid:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid status '{new_status}'. "
                f"Allowed values: {sorted(all_valid)}"
            ),
        )

    # Find the order by ObjectId or custom_order_id
    order_doc = None
    try:
        order_doc = await orders_collection.find_one({"_id": ObjectId(order_id)})
    except Exception:
        order_doc = await orders_collection.find_one({"custom_order_id": order_id})

    if not order_doc:
        raise HTTPException(status_code=404, detail="Order not found")

    current_status = order_doc.get("order_status", "pending")

    # Check that the requested transition is valid from the current status
    allowed_next = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_next:
        if not allowed_next:
            detail = f"Order is already '{current_status}' (terminal state). No further updates allowed."
        else:
            detail = (
                f"Cannot transition from '{current_status}' to '{new_status}'. "
                f"From '{current_status}', only allowed: {allowed_next}"
            )
        raise HTTPException(status_code=400, detail=detail)

    # Apply the update
    try:
        result = await orders_collection.update_one(
            {"_id": order_doc["_id"]},
            {
                "$set": {
                    "order_status": new_status,
                    "updated_at": now_ist(),
                }
            },
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update order status")

        # Clear cache
        await clear_orders_routers_cache()

        return {
            "status": "success",
            "message": TRANSITION_MESSAGES.get(new_status, f"Order status updated to '{new_status}'"),
            "order_id": str(order_doc.get("_id")),
            "custom_order_id": order_doc.get("custom_order_id"),
            "previous_status": current_status,
            "new_status": new_status,
            "updated_at": now_ist(),
            "email": order_doc.get("user_email", "Guest"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update order: {str(e)}")


# ─────────────────────────────────────────────────────────────
# GET order by MongoDB ObjectId
# ─────────────────────────────────────────────────────────────
@orders_router.get("/order/{order_id}", summary="Get full order details by ObjectId")
async def get_order_by_id(
    order_id: str,
    current_admin=Depends(get_current_admin),
):
    """
    Fetch full details of a single order using its MongoDB ObjectId.
    Accessible by admin only.
    """
    # Validate ObjectId format
    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid order id format: '{order_id}'"
        )

    order_doc = await orders_collection.find_one({"_id": ObjectId(order_id)})

    if not order_doc:
        raise HTTPException(
            status_code=404,
            detail=f"Order with id '{order_id}' not found"
        )

    return {
        "status": "success",
        "order": single_order_data(order_doc),
    }
