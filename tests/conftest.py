from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from slowapi.storage.memory import MemoryStorage

import main
import config.redis_caching as redis_caching
import config.rate_limiter as rate_limiter
import config.jwt_auth.token_creation as token_creation
import routers.admin_registration as admin_registration
import routers.categories_router as categories_router
import routers.products_router as products_router
import routers.uploads_router as uploads_router
import routers.coupons_routers as coupons_routers
import routers.userslogin_routers as userslogin_routers
import routers.cart_router as cart_router
import routers.orders_router as orders_router
import routers.shippingcharges_router as shippingcharges_router
import routers.reviews_router as reviews_router
import routers.dashboard_router as dashboard_router

from tests._fakes import FakeCollection, FakeRedis, FakeS3, FakeRazorpayClient


@pytest.fixture
def fake_db():
    return {
        "admin": FakeCollection(),
        "categories": FakeCollection(),
        "products": FakeCollection(),
        "coupons": FakeCollection(),
        "users": FakeCollection(),
        "carts": FakeCollection(),
        "orders": FakeCollection(),
        "shipping": FakeCollection(),
        "reviews": FakeCollection(),
    }


@pytest.fixture
def client(fake_db, monkeypatch):
    async def _noop():
        return None

    fake_redis = FakeRedis()
    monkeypatch.setattr(main, "create_indexes", _noop)
    monkeypatch.setattr(main, "redis_client", fake_redis)
    monkeypatch.setattr(redis_caching, "redis_client", fake_redis)

    rate_limiter.limiter._storage = MemoryStorage()
    main.app.state.limiter = rate_limiter.limiter

    admin_registration.admin_registartion_collection = fake_db["admin"]
    categories_router.categories_collection = fake_db["categories"]
    categories_router.products_collection = fake_db["products"]
    products_router.products_collection = fake_db["products"]
    products_router.categories_collection = fake_db["categories"]
    products_router.reviews_collection = fake_db["reviews"]
    coupons_routers.coupons_collection = fake_db["coupons"]
    userslogin_routers.users_collection = fake_db["users"]
    cart_router.carts_collection = fake_db["carts"]
    cart_router.coupons_collection = fake_db["coupons"]
    orders_router.orders_collection = fake_db["orders"]
    orders_router.carts_collection = fake_db["carts"]
    orders_router.users_collection = fake_db["users"]
    orders_router.products_collection = fake_db["products"]
    orders_router.shipping_charges = fake_db["shipping"]
    shippingcharges_router.shipping_charges = fake_db["shipping"]
    reviews_router.reviews_collection = fake_db["reviews"]
    dashboard_router.orders_collection = fake_db["orders"]
    token_creation.admin_registartion_collection = fake_db["admin"]

    fake_s3 = FakeS3()
    uploads_router.s3 = fake_s3
    products_router.s3 = fake_s3
    reviews_router.s3 = fake_s3

    orders_router.razorpay_client = FakeRazorpayClient()

    async def _send_otp_email(email: str, otp: str):
        return None

    async def _send_order_confirmation_email(user_email: str, order: dict):
        return None

    userslogin_routers.send_otp_email = _send_otp_email
    orders_router.send_order_confirmation_email = _send_order_confirmation_email

    def _fake_create_access_token(payload, expires_minutes=None):
        return "testtoken"

    def _fake_decode_access_token(token):
        if token == "admin-token":
            return {"email": "admin@example.com", "id": "admin-id"}
        return {"email": "user@example.com"}

    token_creation.create_access_token = _fake_create_access_token
    token_creation.decode_access_token = _fake_decode_access_token
    cart_router.decode_access_token = _fake_decode_access_token
    userslogin_routers.decode_access_token = _fake_decode_access_token

    return TestClient(main.app)


@pytest.fixture
def sample_admin(fake_db):
    return fake_db["admin"].insert_one_sync(
        {
            "fullname": "Admin One",
            "mobile": "9999999999",
            "email": "admin@example.com",
            "password": "pass1234",
        }
    )


@pytest.fixture
def sample_category(fake_db):
    return fake_db["categories"].insert_one_sync(
        {
            "name": "Snacks",
            "business_type": "retail",
            "subcategory": [{"name": "Chips"}, {"name": "Mix"}],
            "admin_id": "admin-1",
        }
    )


@pytest.fixture
def sample_product(fake_db, sample_category):
    return fake_db["products"].insert_one_sync(
        {
            "product_name": "Masala Chips",
            "description": "Spicy",
            "images_url": ["https://example.com/img.png"],
            "business_type": "retail",
            "category_id": str(sample_category["_id"]),
            "subcategory": "Chips",
            "pricing": [{"weight": "100g", "price": 50.0, "stock": 10}],
            "is_active": True,
            "admin_id": "admin-1",
        }
    )


@pytest.fixture
def sample_coupon(fake_db):
    return fake_db["coupons"].insert_one_sync(
        {
            "couponcode": "save10",
            "coupon_type": "fixed",
            "value": 10.0,
            "maximum_discount": None,
            "minimum_bill": None,
            "is_active": True,
            "expire_date": None,
            "admin_id": "admin-1",
        }
    )


@pytest.fixture
def sample_cart(fake_db, sample_product):
    return fake_db["carts"].insert_one_sync(
        {
            "guest_id": "guest-123",
            "items": [
                {
                    "product_id": str(sample_product["_id"]),
                    "product_name": "Masala Chips",
                    "image_url": "https://example.com/img.png",
                    "weight": "100g",
                    "price": 50.0,
                    "quantity": 2,
                    "business_type": "retail",
                }
            ],
            "coupon_code": None,
            "discount_amount": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )


@pytest.fixture
def sample_shipping_config(fake_db):
    return fake_db["shipping"].insert_one_sync(
        {
            "admin_id": "admin-1",
            "country": "India",
            "states": [
                {
                    "state_name": "Telangana",
                    "zones": [
                        {
                            "start_zipcode": 500001,
                            "end_zipcode": 500999,
                            "charge_per_kg": 10.0,
                            "free_delivery_min_order_value": 500.0,
                        }
                    ],
                }
            ],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )


@pytest.fixture
def sample_user(fake_db):
    return fake_db["users"].insert_one_sync(
        {
            "email": "user@example.com",
            "otp": "123456",
            "otp_expires_at": datetime.utcnow() + timedelta(minutes=5),
            "otp_attempts": 0,
            "is_verified": False,
        }
    )
