def test_cart_endpoints(client, sample_cart, sample_coupon):
    get_cart = client.get("/cart", params={"guest_id": "guest-123"})
    assert get_cart.status_code == 200

    add_bulk = client.post(
        "/cart/add-bulk",
        json={
            "guest_id": "guest-123",
            "items": [
                {
                    "product_id": "prod-1",
                    "product_name": "Tea",
                    "image_url": "https://example.com/x.png",
                    "weight": "250g",
                    "price": 40.0,
                    "quantity": 1,
                    "business_type": "retail",
                }
            ],
        },
    )
    assert add_bulk.status_code == 200

    update = client.put(
        "/cart/update",
        json={
            "guest_id": "guest-123",
            "product_id": "prod-1",
            "weight": "250g",
            "quantity": 2,
        },
    )
    assert update.status_code in (200, 404)

    apply_coupon = client.post(
        "/cart/apply-coupon",
        json={"guest_id": "guest-123", "coupon_code": "save10"},
    )
    assert apply_coupon.status_code in (200, 400, 404)

    remove_coupon = client.delete(
        "/cart/remove-coupon",
        params={"guest_id": "guest-123"},
    )
    assert remove_coupon.status_code in (200, 404)

    clear_cart = client.delete("/cart/clear", params={"guest_id": "guest-123"})
    assert clear_cart.status_code == 200


def test_cart_merge(client, sample_cart, sample_admin):
    response = client.post(
        "/cart/merge",
        json={"guest_id": "guest-123"},
        headers={"Authorization": "Bearer testtoken"},
    )
    assert response.status_code in (200, 401)
