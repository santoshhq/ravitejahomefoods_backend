def test_categories_real(client, admin_payload):
    admin = client.post("/admin-registration/create", json=admin_payload).json()["data"]

    create_payload = {
        "name": "TestCategory",
        "business_type": "retail",
        "subcategory": [{"name": "Sub1"}],
        "admin_id": admin["id"],
    }
    create = client.post("/categories/create", json=create_payload)
    assert create.status_code == 200

    list_all = client.get("/categories/")
    assert list_all.status_code == 200

    by_admin = client.get(f"/categories/by-admin/{admin['id']}")
    assert by_admin.status_code == 200

    by_name = client.get("/categories/by-name/TestCategory/subcategories")
    assert by_name.status_code == 200

    by_business = client.get(
        "/categories/by-business-type/retail",
        params={"admin_id": admin["id"]},
    )
    assert by_business.status_code == 200

    category_id = create.json()["data"]["id"]
    get_one = client.get(f"/categories/{category_id}")
    assert get_one.status_code == 200

    update = client.put(f"/categories/{category_id}", json={"name": "TestCategory2"})
    assert update.status_code == 200

    all_categories = client.get("/categories/all_Categories/retail")
    assert all_categories.status_code == 200

    delete = client.delete(f"/categories/{category_id}")
    assert delete.status_code == 200
