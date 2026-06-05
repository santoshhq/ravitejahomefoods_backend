from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from prometheus_fastapi_instrumentator import Instrumentator

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config.mongo_indexes import create_indexes
from config.rate_limiter import limiter
from config.redis_caching import redis_client

from routers.admin_registration import admin_registration_router
from routers.categories_router import categories_router
from routers.products_router import products_router
from routers.uploads_router import upload_router
from routers.coupons_routers import coupon_router
from routers.userslogin_routers import userlogin_router
from routers.cart_router import cart_router
from routers.orders_router import orders_router
from routers.shippingcharges_router import shipping_router
from routers.reviews_router import reviews_router
from routers.dashboard_router import dashboard_router
from routers.issues_router import issues_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    try:
        await create_indexes()
        print("✅ Mongo indexes created")
        print("✅ Redis Connected")

    except Exception as e:
        print(f"❌ Startup Error: {e}")

    yield

    # SHUTDOWN
    try:
        await redis_client.close()
        print("❌ Redis Connection Closed")
    except Exception as e:
        print(f"❌ Redis Close Error: {e}")


app = FastAPI(
    title="RaviTeja Foods Backend",
    lifespan=lifespan,
)

# ──────────────────────────────────────────────────────────
# PROMETHEUS METRICS
# ──────────────────────────────────────────────────────────

Instrumentator().instrument(app).expose(app)

# ──────────────────────────────────────────────────────────
# RATE LIMITER
# ──────────────────────────────────────────────────────────

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.add_middleware(SlowAPIMiddleware)

# ──────────────────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://ravitejahomefoods.in",
        "https://www.ravitejahomefoods.in",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────
# HEALTH CHECK
# ──────────────────────────────────────────────────────────

@app.get("/")
async def health_check():
    return {"message": "Raviteja Foods Backend is running"}

# ──────────────────────────────────────────────────────────
# ROUTERS
# ──────────────────────────────────────────────────────────

app.include_router(admin_registration_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(upload_router)
app.include_router(coupon_router)
app.include_router(userlogin_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(shipping_router)
app.include_router(reviews_router)
app.include_router(dashboard_router)
app.include_router(issues_router)