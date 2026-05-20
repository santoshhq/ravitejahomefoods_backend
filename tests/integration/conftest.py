import os
import uuid
import asyncio
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient


os.environ.setdefault("DB_NAME", "RaviTejaFoods_test")

import main
import config.collection as collection
import routers.userslogin_routers as userslogin_routers
import routers.orders_router as orders_router


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(scope="session")
def client():
    return TestClient(main.app)


@pytest.fixture(autouse=True)
def cleanup_db():
    async def _cleanup():
        await collection.admin_registartion_collection.delete_many({})
        await collection.categories_collection.delete_many({})
        await collection.products_collection.delete_many({})
        await collection.coupons_collection.delete_many({})
        await collection.users_collection.delete_many({})
        await collection.carts_collection.delete_many({})
        await collection.orders_collection.delete_many({})
        await collection.shipping_charges.delete_many({})
        await collection.reviews_collection.delete_many({})

    _run(_cleanup())
    yield
    _run(_cleanup())


@pytest.fixture
def admin_payload():
    return {
        "fullname": "Admin Real",
        "mobile": "9999999999",
        "email": f"admin+{uuid.uuid4().hex[:8]}@example.com",
        "password": "pass1234",
    }


@pytest.fixture
def user_email():
    return f"user+{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture(autouse=True)
def disable_external_email(monkeypatch):
    async def _noop_send_otp_email(email: str, otp: str):
        return None

    async def _noop_send_order_confirmation_email(user_email: str, order: dict):
        return None

    monkeypatch.setattr(userslogin_routers, "send_otp_email", _noop_send_otp_email)
    monkeypatch.setattr(orders_router, "send_order_confirmation_email", _noop_send_order_confirmation_email)


@pytest.fixture
def shipping_payload():
    return {
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
    }


@pytest.fixture
def low_price_product_payload():
    return {
        "product_name": "TEST_LOW_PRICE",
        "description": "Test product",
        "business_type": "retail",
        "subcategory": "Test",
        "pricing": "[{\"weight\": \"100g\", \"price\": 1.0, \"stock\": 10}]",
        "is_active": "true",
        "image_urls": "[]",
    }


@pytest.fixture
def otp_doc(user_email):
    return {
        "email": user_email,
        "otp": "123456",
        "otp_expires_at": datetime.utcnow() + timedelta(minutes=5),
        "otp_attempts": 0,
        "is_verified": False,
    }
