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


def test_reviews_pagination(client, sample_product):
    product_id = str(sample_product["_id"])
    
    # Create 3 reviews for the product
    for i in range(1, 4):
        create = client.post(
            "/reviews/create_review",
            data={
                "product_id": product_id,
                "rating": i,
                "review_title": f"Title {i}",
                "review_content": f"Content {i}",
                "display_name": f"User {i}",
                "email_address": f"user{i}@example.com",
                "mobile_number": f"999999990{i}",
                "is_active": "true",
            },
        )
        assert create.status_code == 201

    # Get first page (limit=2, skip=0)
    page1 = client.get(f"/reviews/product/{product_id}/paginated?skip=0&limit=2")
    assert page1.status_code == 200
    res1 = page1.json()
    assert res1["count"] == 3
    assert len(res1["data"]) == 2
    assert res1["has_next"] is True
    assert res1["next_skip"] == 2
    assert res1["avg_rating"] == 2.0

    # Get second page (limit=2, skip=2)
    page2 = client.get(f"/reviews/product/{product_id}/paginated?skip=2&limit=2")
    assert page2.status_code == 200
    res2 = page2.json()
    assert res2["count"] == 3
    assert len(res2["data"]) == 1
    assert res2["has_next"] is False
    assert res2["next_skip"] is None

