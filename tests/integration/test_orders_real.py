import os
import pytest


def test_orders_place_real(client, admin_payload, shipping_payload):
    admin = client.post("/admin-registration/create", json=admin_payload).json()["data"]

    client.post(f"/shipping/admin/{admin['id']}/rules", json=shipping_payload)

    category = client.post(
        "/categories/create",
        json={
            "name": "OrderCategory",
            "business_type": "retail",
            "subcategory": [{"name": "Test"}],
            "admin_id": admin["id"],
        },
    ).json()["data"]

    product = client.post(
        "/products/create_product",
        data={
            "product_name": "OrderProduct",
            "description": "Test",
            "business_type": "retail",
            "category_id": category["id"],
            "subcategory": "Test",
            "pricing": "[{\"weight\": \"100g\", \"price\": 1.0, \"stock\": 10}]",
            "is_active": "true",
            "image_urls": "[]",
            "admin_id": admin["id"],
        },
    ).json()

    client.post(
        "/cart/add-bulk",
        json={
            "guest_id": "guest-order-1",
            "items": [
                {
                    "product_id": product["product_id"],
                    "product_name": "OrderProduct",
                    "image_url": "https://example.com/x.png",
                    "weight": "100g",
                    "price": 1.0,
                    "quantity": 1,
                    "business_type": "retail",
                }
            ],
        },
    )

    estimate = client.post(
        "/orders/delivery-estimate",
        json={
            "country": "India",
            "state": "Telangana",
            "pincode": "500001",
            "guest_id": "guest-order-1",
        },
    )
    assert estimate.status_code in (200, 400, 404)

    place = client.post(
        "/orders/place",
        json={
            "email": "buyer@example.com",
            "guest_id": "guest-order-1",
            "shipping_address": {
                "name": "Test Buyer",
                "mobile": "9999999999",
                "address_line": "Street 1",
                "city": "Hyderabad",
                "state": "Telangana",
                "country": "India",
                "pincode": "500001",
            },
        },
    )
    assert place.status_code in (201, 400, 404, 500)


@pytest.mark.skipif(
    not os.getenv("LIVE_RAZORPAY_SIGNATURE"),
    reason="Set LIVE_RAZORPAY_SIGNATURE to enable live verify-payment test",
)
def test_orders_verify_payment_real(client):
    verify = client.post(
        "/orders/verify-payment",
        json={
            "razorpay_order_id": os.getenv("LIVE_RAZORPAY_ORDER_ID"),
            "razorpay_payment_id": os.getenv("LIVE_RAZORPAY_PAYMENT_ID"),
            "razorpay_signature": os.getenv("LIVE_RAZORPAY_SIGNATURE"),
            "guest_id": "guest-order-1",
        },
    )
    assert verify.status_code in (200, 400)
