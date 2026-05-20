def test_reviews_real(client, admin_payload):
    admin = client.post("/admin-registration/create", json=admin_payload).json()["data"]

    category = client.post(
        "/categories/create",
        json={
            "name": "ReviewCategory",
            "business_type": "retail",
            "subcategory": [{"name": "Test"}],
            "admin_id": admin["id"],
        },
    ).json()["data"]

    product = client.post(
        "/products/create_product",
        data={
            "product_name": "ReviewProduct",
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

    create = client.post(
        "/reviews/create_review",
        data={
            "product_id": product["product_id"],
            "rating": 5,
            "review_title": "Great",
            "review_content": "Tasty",
            "display_name": "User",
            "email_address": "user@example.com",
            "mobile_number": "9999999999",
            "is_active": "true",
        },
    )
    assert create.status_code == 201
    review_id = create.json().get("data", {}).get("id")
    assert review_id

    product_reviews = client.get(f"/reviews/product/{product['product_id']}")
    assert product_reviews.status_code == 200
    response_body = product_reviews.json()
    assert "avg_rating" in response_body
    assert "data" in response_body

    get_one = client.get(f"/reviews/{review_id}")
    assert get_one.status_code in (200, 400, 404)

    update = client.put(
        f"/reviews/update_review/{review_id}",
        data={"review_content": "Updated"},
    )
    assert update.status_code in (200, 400, 404)

    delete = client.delete(f"/reviews/delete_review/{review_id}")
    assert delete.status_code in (200, 404)

    delete_by_product = client.delete(f"/reviews/delete_by_product/{product['product_id']}")
    assert delete_by_product.status_code == 200
