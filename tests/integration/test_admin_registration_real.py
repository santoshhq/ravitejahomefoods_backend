def test_admin_registration_real(client, admin_payload):
    create = client.post("/admin-registration/create", json=admin_payload)
    assert create.status_code == 201

    login = client.post(
        "/admin-registration/login",
        data={"username": admin_payload["email"], "password": admin_payload["password"]},
    )
    assert login.status_code == 200
    token = login.json().get("access_token")
    assert token

    refresh = client.post(
        "/admin-registration/refresh",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert refresh.status_code == 200

    user_id = create.json()["data"]["id"]
    update = client.put(
        f"/admin-registration/update-registration/{user_id}",
        json={"fullname": "Admin Real Updated"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update.status_code == 200
