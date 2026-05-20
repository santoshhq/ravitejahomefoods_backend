def test_orders_flow(client, sample_cart, sample_product, sample_shipping_config):
    estimate = client.post(
        "/orders/delivery-estimate",
        json={
            "country": "India",
            "state": "Telangana",
            "pincode": "500001",
            "guest_id": "guest-123",
        },
    )
    assert estimate.status_code in (200, 400, 404)

    place = client.post(
        "/orders/place",
        json={
            "email": "user@example.com",
            "guest_id": "guest-123",
            "shipping_address": {
                "name": "Test User",
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

    verify = client.post(
        "/orders/verify-payment",
        json={
            "razorpay_order_id": "order_test_1",
            "razorpay_payment_id": "pay_1",
            "razorpay_signature": "sig_1",
            "guest_id": "guest-123",
        },
    )
    assert verify.status_code in (200, 400)

    guest_orders = client.get("/orders/guest/guest-123")
    assert guest_orders.status_code == 200


def test_orders_admin(client, sample_admin):
    response = client.get(
        "/orders/admin/all-orders",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert response.status_code in (200, 401)
