import json


def test_products_real(client, admin_payload, low_price_product_payload):
    admin = client.post("/admin-registration/create", json=admin_payload).json()["data"]

    category = client.post(
        "/categories/create",
        json={
            "name": "TestCategory",
            "business_type": "retail",
            "subcategory": [{"name": "Test"}],
            "admin_id": admin["id"],
        },
    ).json()["data"]

    product_payload = dict(low_price_product_payload)
    product_payload["category_id"] = category["id"]
    product_payload["admin_id"] = admin["id"]

    create = client.post("/products/create_product", data=product_payload)
    assert create.status_code == 200
    product_id = create.json()["product_id"]

    all_products = client.get("/products/all")
    assert all_products.status_code == 200

    active = client.get("/products/get_active_products")
    assert active.status_code == 200

    active_by_category = client.get(
        "/products/active-by-category",
        params={"category_id": category["id"], "subcategory": "Test"},
    )
    assert active_by_category.status_code == 200

    by_admin = client.get(f"/products/by-admin/{admin['id']}")
    assert by_admin.status_code == 200

    get_one = client.get(f"/products/get_product/{product_id}")
    assert get_one.status_code == 200

    update = client.put(
        f"/products/update_product/{product_id}",
        data={"description": "Updated"},
    )
    assert update.status_code == 200

    by_business = client.get("/products/business_type_products/retail")
    assert by_business.status_code == 200

    delete = client.delete(f"/products/delete_product/{product_id}")
    assert delete.status_code == 200
