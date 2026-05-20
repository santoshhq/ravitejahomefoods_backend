def test_admin_create(client):
    payload = {
        "fullname": "Admin Two",
        "mobile": "8888888888",
        "email": "admin2@example.com",
        "password": "pass1234",
    }
    response = client.post("/admin-registration/create", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data.get("message")
    assert data.get("data")


def test_admin_login(client, sample_admin):
    response = client.post(
        "/admin-registration/login",
        data={"username": "admin@example.com", "password": "pass1234"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("access_token")


def test_admin_refresh(client, sample_admin):
    response = client.post(
        "/admin-registration/refresh",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert response.status_code == 200
    assert response.json().get("access_token")


def test_admin_update(client, sample_admin):
    user_id = str(sample_admin["_id"])
    response = client.put(
        f"/admin-registration/update-registration/{user_id}",
        json={"fullname": "Admin Updated"},
        headers={"Authorization": "Bearer admin-token"},
    )
    assert response.status_code == 200
    assert response.json().get("data")
