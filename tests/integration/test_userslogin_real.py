import config.collection as collection


def test_userslogin_real(client, user_email, otp_doc):
    collection.users_collection.insert_one(otp_doc)

    request_otp = client.post("/user-login/request-otp", json={"email": user_email})
    assert request_otp.status_code == 200

    verify = client.post(
        "/user-login/verify-otp",
        json={"email": user_email, "otp": "123456"},
    )
    assert verify.status_code == 200

    token = verify.json().get("access_token")
    me = client.get("/user-login/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code in (200, 404)
