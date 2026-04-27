from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from datetime import datetime
from jose import JWTError

from config.collection import carts_collection, coupons_collection
from models.cart_model import (
    BulkAddToCartRequest,
    UpdateCartItemRequest,
    ApplyCouponRequest,
    RemoveCouponRequest,
    MergeCartRequest,
)
from schemas.cart_schema import cart_data
from config.jwt_auth.token_creation import decode_access_token

cart_router = APIRouter(prefix="/cart", tags=["Cart"])

# ── Auth helpers ────────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/user-login/verify-otp", auto_error=False
)


async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """Returns user email if JWT is valid, else None (guest user)."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        return payload.get("email")
    except (JWTError, Exception):
        return None


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> str:
    """Strict auth — raises 401 if no valid JWT."""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = decode_access_token(token)
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except (JWTError, Exception):
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── Internal helpers ─────────────────────────────────────────────────────────

def resolve_query(user_email: Optional[str], guest_id: Optional[str]) -> dict:
    """Build the MongoDB filter based on who is calling."""
    if user_email:
        return {"user_email": user_email}
    if guest_id:
        return {"guest_id": guest_id}
    raise HTTPException(
        status_code=400,
        detail="Provide a Bearer token (logged-in) or a guest_id (guest user)",
    )


# ── GET /cart ────────────────────────────────────────────────────────────────

@cart_router.get(
    "/",
    response_model=dict,
    name="cart:get-cart",
    summary="Get the current cart (guest or logged-in user)",
)
async def get_cart(
    guest_id: Optional[str] = Query(default=None),
    current_user: Optional[str] = Depends(get_optional_user),
):
    query = resolve_query(current_user, guest_id)
    cart = await carts_collection.find_one(query)
    if not cart:
        return {"data": None, "message": "Cart is empty"}
    return {"data": cart_data(cart)}


# ── POST /cart/add-bulk ──────────────────────────────────────────────────────

@cart_router.post(
    "/add-bulk",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    name="cart:add-bulk",
    summary="Add multiple items to cart in one request",
)
async def add_bulk_to_cart(
    req: BulkAddToCartRequest,
    current_user: Optional[str] = Depends(get_optional_user),
):
    query = resolve_query(current_user, req.guest_id)
    now = datetime.utcnow()
    added = []
    skipped = []

    for item in req.items:
        item_dict = item.model_dump()

        # Check if same product + weight already exists in cart
        existing_cart = await carts_collection.find_one({
            **query,
            "items": {
                "$elemMatch": {
                    "product_id": item.product_id,
                    "weight": item.weight,
                }
            },
        })

        if existing_cart:
            # Increment quantity
            await carts_collection.update_one(
                {
                    **query,
                    "items.product_id": item.product_id,
                    "items.weight": item.weight,
                },
                {
                    "$inc": {"items.$.quantity": item.quantity},
                    "$set": {"updated_at": now},
                },
            )
            added.append(f"{item.product_name} ({item.weight}) — qty updated")
        else:
            # Push new item (upsert cart doc if first item ever)
            await carts_collection.update_one(
                query,
                {
                    "$push": {"items": item_dict},
                    "$set": {"updated_at": now},
                    "$setOnInsert": {
                        "coupon_code": None,
                        "discount_amount": 0.0,
                        "created_at": now,
                    },
                },
                upsert=True,
            )
            added.append(f"{item.product_name} ({item.weight}) — added")

    updated_cart = await carts_collection.find_one(query)
    return {
        "message": f"{len(added)} item(s) processed",
        "summary": added,
        "data": cart_data(updated_cart),
    }


# ── PUT /cart/update ─────────────────────────────────────────────────────────

@cart_router.put(
    "/update",
    response_model=dict,
    name="cart:update-item",
    summary="Update quantity of a cart item (quantity=0 removes the item)",
)
async def update_cart_item(
    req: UpdateCartItemRequest,
    current_user: Optional[str] = Depends(get_optional_user),
):
    query = resolve_query(current_user, req.guest_id)

    if req.quantity == 0:
        # Remove the item entirely
        await carts_collection.update_one(
            query,
            {
                "$pull": {
                    "items": {
                        "product_id": req.product_id,
                        "weight": req.weight,
                    }
                },
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
        updated_cart = await carts_collection.find_one(query)
        if not updated_cart:
            return {"message": "Item removed, cart is now empty", "data": None}
        return {"message": "Item removed", "data": cart_data(updated_cart)}

    # Set the exact quantity
    result = await carts_collection.update_one(
        {
            **query,
            "items.product_id": req.product_id,
            "items.weight": req.weight,
        },
        {
            "$set": {
                "items.$.quantity": req.quantity,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    updated_cart = await carts_collection.find_one(query)
    return {"message": "Cart updated", "data": cart_data(updated_cart)}


# ── DELETE /cart/clear ───────────────────────────────────────────────────────

@cart_router.delete(
    "/clear",
    response_model=dict,
    name="cart:clear",
    summary="Empty the entire cart",
)
async def clear_cart(
    guest_id: Optional[str] = Query(default=None),
    current_user: Optional[str] = Depends(get_optional_user),
):
    query = resolve_query(current_user, guest_id)
    await carts_collection.delete_one(query)
    return {"message": "Cart cleared successfully"}


# ── POST /cart/apply-coupon ───────────────────────────────────────────────────

@cart_router.post(
    "/apply-coupon",
    response_model=dict,
    name="cart:apply-coupon",
    summary="Apply a coupon code and preview the discount",
)
async def apply_coupon(
    req: ApplyCouponRequest,
    current_user: Optional[str] = Depends(get_optional_user),
):
    query = resolve_query(current_user, req.guest_id)

    # Fetch cart
    cart = await carts_collection.find_one(query)
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Validate coupon from DB
    coupon = await coupons_collection.find_one({
        "couponcode": req.coupon_code.strip().lower(),
        "is_active": True,
    })
    if not coupon:
        raise HTTPException(status_code=404, detail="Invalid or inactive coupon code")

    # Check expiry
    expire_date = coupon.get("expire_date")
    if expire_date:
        from datetime import date
        try:
            exp = datetime.strptime(expire_date, "%Y-%m-%d").date()
            if date.today() > exp:
                raise HTTPException(status_code=400, detail="Coupon has expired")
        except ValueError:
            pass  # skip if date format unexpected

    # Calculate subtotal
    subtotal = sum(
        i.get("price", 0) * i.get("quantity", 0) for i in cart.get("items", [])
    )

    # Check minimum bill
    min_bill = coupon.get("minimum_bill")
    if min_bill and subtotal < min_bill:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum bill of ₹{min_bill} required to use this coupon",
        )

    # Calculate discount
    if coupon["coupon_type"] == "percentage":
        discount = round(subtotal * coupon["value"] / 100, 2)
        max_discount = coupon.get("maximum_discount")
        if max_discount:
            discount = min(discount, max_discount)
    else:  # fixed
        discount = round(min(coupon["value"], subtotal), 2)

    # Save coupon to cart (preview only — final validation happens at order)
    await carts_collection.update_one(
        query,
        {
            "$set": {
                "coupon_code": req.coupon_code.strip().lower(),
                "discount_amount": discount,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    updated_cart = await carts_collection.find_one(query)
    return {
        "message": f"Coupon applied! You save ₹{discount}",
        "data": cart_data(updated_cart),
    }


# ── DELETE /cart/remove-coupon ────────────────────────────────────────────────

@cart_router.delete(
    "/remove-coupon",
    response_model=dict,
    name="cart:remove-coupon",
    summary="Remove applied coupon from cart",
)
async def remove_coupon(
    guest_id: Optional[str] = Query(default=None),
    current_user: Optional[str] = Depends(get_optional_user),
):
    query = resolve_query(current_user, guest_id)
    await carts_collection.update_one(
        query,
        {
            "$set": {
                "coupon_code": None,
                "discount_amount": 0.0,
                "updated_at": datetime.utcnow(),
            }
        },
    )
    updated_cart = await carts_collection.find_one(query)
    if not updated_cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return {"message": "Coupon removed", "data": cart_data(updated_cart)}


# ── POST /cart/merge ──────────────────────────────────────────────────────────

@cart_router.post(
    "/merge",
    response_model=dict,
    name="cart:merge",
    summary="Merge guest cart into logged-in user cart (call right after login)",
)
async def merge_cart(
    req: MergeCartRequest,
    current_user: str = Depends(get_current_user),
):
    guest_cart = await carts_collection.find_one({"guest_id": req.guest_id})
    if not guest_cart or not guest_cart.get("items"):
        return {"message": "No guest cart items to merge"}

    now = datetime.utcnow()

    for item in guest_cart.get("items", []):
        # Check if same product + weight already in user cart
        existing = await carts_collection.find_one({
            "user_email": current_user,
            "items": {
                "$elemMatch": {
                    "product_id": item["product_id"],
                    "weight": item["weight"],
                }
            },
        })

        if existing:
            # Merge quantities
            await carts_collection.update_one(
                {
                    "user_email": current_user,
                    "items.product_id": item["product_id"],
                    "items.weight": item["weight"],
                },
                {
                    "$inc": {"items.$.quantity": item["quantity"]},
                    "$set": {"updated_at": now},
                },
            )
        else:
            # Push new item into user cart
            await carts_collection.update_one(
                {"user_email": current_user},
                {
                    "$push": {"items": item},
                    "$set": {"updated_at": now},
                    "$setOnInsert": {
                        "coupon_code": None,
                        "discount_amount": 0.0,
                        "created_at": now,
                    },
                },
                upsert=True,
            )

    # Delete guest cart after merge
    await carts_collection.delete_one({"guest_id": req.guest_id})

    merged_cart = await carts_collection.find_one({"user_email": current_user})
    return {
        "message": "Guest cart merged into your account successfully",
        "data": cart_data(merged_cart) if merged_cart else None,
    }
