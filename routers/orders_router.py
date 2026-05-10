import os
from bson import ObjectId
import razorpay
import httpx
from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.encoders import jsonable_encoder
import random
import string
from datetime import datetime
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
from schemas.order_schema import order_data, all_orders_data
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
            <td style='padding: 8px; border-bottom: 1px solid #eee;'>{item['product_name']} ({item['weight']})</td>
            <td style='padding: 8px; border-bottom: 1px solid #eee;'>{item['quantity']}</td>
            <td style='padding: 8px; border-bottom: 1px solid #eee;'>₹{item['price']}</td>
            <td style='padding: 8px; border-bottom: 1px solid #eee; text-align: right;'>₹{item['price'] * item['quantity']}</td>
        </tr>
        """

    html_content = f"""
    <div style='font-family: sans-serif; color: #333; max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 10px;'>
        <h2 style='color: #E63946; text-align: center;'>Order Confirmed! ✅</h2>
        <p>Hello,</p>
        <p>Thank you for your order from <strong>RaviTeja Foods</strong>. Your payment was successful.</p>
        <hr/>
        <h4>Order Summary</h4>
        <p><strong>Order ID:</strong> {order.get('custom_order_id', order['razorpay_order_id'])}<br/>
        <strong>Payment ID:</strong> {order.get('razorpay_payment_id', 'N/A')}</p>
        <table style='width: 100%; border-collapse: collapse;'>
            <thead>
                <tr style='background: #f8f8f8;'>
                    <th style='text-align: left; padding: 8px;'>Item</th>
                    <th style='text-align: left; padding: 8px;'>Qty</th>
                    <th style='text-align: left; padding: 8px;'>Price</th>
                    <th style='text-align: right; padding: 8px;'>Total</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>
        
        <div style='text-align: right; margin-top: 15px;'>
            <p><strong>Subtotal:</strong> ₹{order['subtotal']}</p>
            <p><strong>Discount ({order.get('coupon_code') or 'None'}):</strong> -₹{order['discount_amount']}</p>
            <p><strong>GST (12%):</strong> ₹{order['gst_amount']}</p>
            <p><strong>Delivery:</strong> ₹{order['delivery_charges']}</p>
            <h3 style='color: #1D3557;'>Grand Total: ₹{order['grand_total']}</h3>
        </div>
        
        <hr/>
        <h4>Delivery Address:</h4>
        <p>
            {order['shipping_address']['name']}<br/>
            {order['shipping_address']['mobile']}<br/>
            {order['shipping_address']['address_line']}, {order['shipping_address']['city']}<br/>
            {order['shipping_address'].get('state', '')}, {order['shipping_address']['country']} - {order['shipping_address']['pincode']}
        </p>
        
        <p style='font-size: 12px; color: #777; text-align: center;'>
            &copy; {datetime.now().year} RaviTeja Foods. All rights reserved.
        </p>
    </div>
    """

    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": "RaviTeja Foods <orders@genxtechnologies.tech>",
                "to": [user_email],
                "subject": f"Order Confirmed - {order.get('custom_order_id', order['razorpay_order_id'])}",
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
                detail="Delivery for retail products is only available for pincodes between 500001 and 500115."
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
        "order_status": "confirmed",
        "payment_status": "paid",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
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
