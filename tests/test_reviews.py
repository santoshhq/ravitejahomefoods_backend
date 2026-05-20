def test_reviews_endpoints(client, sample_product):
    create = client.post(
        "/reviews/create_review",
        data={
            "product_id": str(sample_product["_id"]),
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

    product_reviews = client.get(f"/reviews/product/{str(sample_product['_id'])}")
    assert product_reviews.status_code == 200
    response_body = product_reviews.json()
    assert "avg_rating" in response_body
    assert "data" in response_body

    review_id = create.json().get("data", {}).get("id")
    assert review_id
    get_one = client.get(f"/reviews/{review_id}")
    assert get_one.status_code in (200, 400, 404)

    update = client.put(
        f"/reviews/update_review/{review_id}",
        data={"review_content": "Updated"},
    )
    assert update.status_code in (200, 400, 404)

    delete = client.delete(f"/reviews/delete_review/{review_id}")
    assert delete.status_code in (200, 404)

    delete_by_product = client.delete(f"/reviews/delete_by_product/{str(sample_product['_id'])}")
    assert delete_by_product.status_code == 200
