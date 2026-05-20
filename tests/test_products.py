import json


def test_products_crud(client, sample_product):
    create_payload = {
        "product_name": "Idli",
        "description": "Soft",
        "business_type": "retail",
        "category_id": str(sample_product["_id"]),
        "subcategory": "Chips",
        "pricing": json.dumps([
            {"weight": "250g", "price": 80.0, "stock": 5}
        ]),
        "is_active": "true",
        "image_urls": json.dumps(["https://example.com/p.png"]),
        "admin_id": "admin-1",
    }
    create = client.post("/products/create_product", data=create_payload)
    assert create.status_code == 200

    all_products = client.get("/products/all")
    assert all_products.status_code == 200

    active = client.get("/products/get_active_products")
    assert active.status_code == 200

    active_by_cat = client.get(
        "/products/active-by-category",
        params={"category_id": str(sample_product["_id"]), "subcategory": "Chips"},
    )
    assert active_by_cat.status_code == 200

    by_admin = client.get("/products/by-admin/admin-1")
    assert by_admin.status_code == 200

    product_id = str(sample_product["_id"])
    get_one = client.get(f"/products/get_product/{product_id}")
    assert get_one.status_code in (200, 400)

    update = client.put(
        f"/products/update_product/{product_id}",
        data={"description": "Updated"},
    )
    assert update.status_code == 200

    delete = client.delete(f"/products/delete_product/{product_id}")
    assert delete.status_code == 200

    by_business = client.get("/products/business_type_products/retail")
    assert by_business.status_code == 200
