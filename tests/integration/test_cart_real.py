import config.collection as collection


def test_cart_real(client, admin_payload):
    admin = client.post("/admin-registration/create", json=admin_payload).json()["data"]

    category = client.post(
        "/categories/create",
        json={
            "name": "CartCategory",
            "business_type": "retail",
            "subcategory": [{"name": "Test"}],
            "admin_id": admin["id"],
        },
    ).json()["data"]

    product = client.post(
        "/products/create_product",
        data={
            "product_name": "CartProduct",
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

    add_bulk = client.post(
        "/cart/add-bulk",
        json={
            "guest_id": "guest-real-1",
            "items": [
                {
                    "product_id": product["product_id"],
                    "product_name": "CartProduct",
                    "image_url": "https://example.com/x.png",
                    "weight": "100g",
                    "price": 1.0,
                    "quantity": 1,
                    "business_type": "retail",
                }
            ],
        },
    )
    assert add_bulk.status_code == 200

    get_cart = client.get("/cart", params={"guest_id": "guest-real-1"})
    assert get_cart.status_code == 200

    update = client.put(
        "/cart/update",
        json={
            "guest_id": "guest-real-1",
            "product_id": product["product_id"],
            "weight": "100g",
            "quantity": 2,
        },
    )
    assert update.status_code in (200, 404)

    remove_coupon = client.delete("/cart/remove-coupon", params={"guest_id": "guest-real-1"})
    assert remove_coupon.status_code in (200, 404)

    clear_cart = client.delete("/cart/clear", params={"guest_id": "guest-real-1"})
    assert clear_cart.status_code == 200
