def test_categories_crud(client, sample_category):
    create_payload = {
        "name": "Beverages",
        "business_type": "retail",
        "subcategory": [{"name": "Tea"}],
        "admin_id": "admin-1",
    }
    create_response = client.post("/categories/create", json=create_payload)
    assert create_response.status_code == 200

    list_response = client.get("/categories/")
    assert list_response.status_code == 200
    assert list_response.json().get("count") is not None

    by_admin = client.get("/categories/by-admin/admin-1")
    assert by_admin.status_code == 200

    by_name = client.get("/categories/by-name/Snacks/subcategories")
    assert by_name.status_code == 200
    assert by_name.json().get("subcategories")

    by_business = client.get("/categories/by-business-type/retail", params={"admin_id": "admin-1"})
    assert by_business.status_code == 200

    category_id = str(sample_category["_id"])
    get_one = client.get(f"/categories/{category_id}")
    assert get_one.status_code == 200

    update = client.put(f"/categories/{category_id}", json={"name": "Snacks Updated"})
    assert update.status_code == 200

    all_categories = client.get("/categories/all_Categories/retail")
    assert all_categories.status_code == 200

    delete = client.delete(f"/categories/{category_id}")
    assert delete.status_code == 200
