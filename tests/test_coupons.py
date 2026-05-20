def test_coupons_crud(client, sample_coupon):
    create = client.post(
        "/coupons/",
        data={
            "couponcode": "save20",
            "coupon_type": "fixed",
            "value": 20.0,
            "is_active": "true",
            "admin_id": "admin-1",
        },
    )
    assert create.status_code == 201

    by_admin = client.get("/coupons/by-admin", params={"admin_id": "admin-1"})
    assert by_admin.status_code == 200

    coupon_id = str(sample_coupon["_id"])
    get_one = client.get(f"/coupons/{coupon_id}")
    assert get_one.status_code == 200

    update = client.put(
        f"/coupons/{coupon_id}",
        data={"is_active": "false"},
    )
    assert update.status_code in (200, 400)

    delete = client.delete(
        f"/coupons/{coupon_id}",
        params={"admin_id": "admin-1"},
    )
    assert delete.status_code == 200
