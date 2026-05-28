import os
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
# 🔐 Hybrid key: user (token) + fallback IP
def rate_limit_key(request: Request):
    auth = request.headers.get("Authorization")
    if auth:
        return auth   # user-based limiting
    guest_id = request.headers.get("X-Guest-Id")
    if guest_id:
        return f"guest:{guest_id}"
    return get_remote_address(request)  # fallback to IP


# 🌍 Default fallback limit (for unprotected routes)
DEFAULT_RATE_LIMIT = "200/minute"


# 🎯 Centralized limits (burst + sustained)
RATE_LIMITS = {
    # 🔐 Admin
    "admin_create": "5/minute; 20/hour",
    "admin_login": "5/minute; 20/hour",
    "admin_refresh": "30/minute",
    "admin_update": "20/minute",

    # 👤 User auth
    "user_request_otp": "5/minute; 20/hour",
    "user_verify_otp": "5/minute; 10/hour",
    "user_me": "60/minute",

    # 🛒 Cart
    "cart_read": "30/second; 120/minute",
    "cart_write": "10/second; 60/minute",
    "cart_checkout": "5/minute",
    "cart_sensitive": "30/minute",
    "cart_merge": "10/minute",

    # 🎟 Coupons
    "coupon_write": "20/minute",
    "coupon_read": "60/minute",

    # 📂 Categories
    "category_read": "30/second; 120/minute",
    "category_write": "20/minute",

    # 📦 Products
    "product_read": "30/second; 120/minute",
    "product_write": "20/minute",

    # ⭐ Reviews
    "review_read": "60/minute",
    "review_write": "20/minute",

    # 📊 Dashboard
    "dashboard_read": "30/minute",

    # 📤 Uploads
    "upload_write": "10/minute",
    "upload_read": "60/minute",
    "upload_list": "30/minute",

    # 📦 Orders
    "order_estimate": "60/minute",
    "order_place": "5/minute",
    "order_verify": "5/minute",
    "order_read": "60/minute",

    # 🚚 Shipping
    "shipping_write": "10/minute",
    "shipping_read": "60/minute",
    "shipping_public": "120/minute",
}


# 🔗 Redis (for production scaling)

storage_uri="redis://redis:6379/1"
limiter = Limiter(
    key_func=rate_limit_key,
    default_limits=[DEFAULT_RATE_LIMIT],
    storage_uri=storage_uri,
)
