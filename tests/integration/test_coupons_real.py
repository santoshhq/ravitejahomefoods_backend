def test_coupons_real(client, admin_payload):
    admin = client.post("/admin-registration/create", json=admin_payload).json()["data"]

    create = client.post(
        "/coupons/",
        data={
            "couponcode": "save10",
            "coupon_type": "fixed",
            "value": 1.0,
            "is_active": "true",
            "admin_id": admin["id"],
        },
    )
    assert create.status_code == 201
    coupon_id = create.json()["data"]["id"]

    by_admin = client.get("/coupons/by-admin", params={"admin_id": admin["id"]})
    assert by_admin.status_code == 200

    get_one = client.get(f"/coupons/{coupon_id}")
    assert get_one.status_code == 200

    update = client.put(f"/coupons/{coupon_id}", data={"is_active": "false"})
    assert update.status_code in (200, 400)

    delete = client.delete(f"/coupons/{coupon_id}", params={"admin_id": admin["id"]})
    assert delete.status_code == 200
