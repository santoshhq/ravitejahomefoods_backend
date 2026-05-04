from routers.admin_registration import admin_registration_router
from config.collection import admin_registartion_collection, carts_collection
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import ASCENDING
from routers.categories_router import categories_router
from routers.products_router import products_router
from routers.uploads_router import upload_router
from routers.coupons_routers import coupon_router
from routers.userslogin_routers import userlogin_router
from routers.cart_router import cart_router
from routers.orders_router import orders_router
from routers.shippingcharges_router import shipping_router
from config.rate_limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

app = FastAPI(title="RaviTeja Foods Backend")
# ── RATE_LIMITER ──────────────────────────────────────────────────────────
app.state.limiter=limiter
app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
# ── CORS ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)


@app.on_event("startup")
async def bootstrap_indexes():
    await admin_registartion_collection.create_index(
        [("email", ASCENDING)],
        unique=True,
        name="uniq_admin_email",
    )
    # Cart indexes
    await carts_collection.create_index("user_email", sparse=True, name="idx_cart_user_email")
    await carts_collection.create_index("guest_id", sparse=True, name="idx_cart_guest_id")
    # TTL index: auto-delete abandoned guest carts after 7 days
    await carts_collection.create_index(
        "updated_at",
        expireAfterSeconds=604800,
        name="ttl_cart_updated_at",
    )


@app.get("/")
async def health_check():
    return {"message": "Raviteja Foods Backend is running"}


app.include_router(admin_registration_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(upload_router)
app.include_router(coupon_router)
app.include_router(userlogin_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(shipping_router)
