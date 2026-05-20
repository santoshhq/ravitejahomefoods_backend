def test_userlogin_flow(client, sample_user):
    request_otp = client.post("/user-login/request-otp", json={"email": "user@example.com"})
    assert request_otp.status_code == 200

    verify = client.post(
        "/user-login/verify-otp",
        json={"email": "user@example.com", "otp": "123456"},
    )
    assert verify.status_code == 200
    assert verify.json().get("access_token")

    me = client.get("/user-login/me", headers={"Authorization": "Bearer testtoken"})
    assert me.status_code in (200, 404)
