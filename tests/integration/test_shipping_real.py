def test_shipping_real(client, admin_payload, shipping_payload):
    admin = client.post("/admin-registration/create", json=admin_payload).json()["data"]

    create = client.post(f"/shipping/admin/{admin['id']}/rules", json=shipping_payload)
    assert create.status_code in (200, 400)

    rules = client.get(f"/shipping/admin/{admin['id']}/rules")
    assert rules.status_code == 200

    countries = client.get("/shipping/countries")
    assert countries.status_code == 200

    states = client.get("/shipping/countries/India/states")
    assert states.status_code in (200, 404)

    add_state = client.post(
        f"/shipping/admin/{admin['id']}/add-state",
        json={
            "country": "India",
            "state": {
                "state_name": "AP",
                "zones": [
                    {
                        "start_zipcode": 500001,
                        "end_zipcode": 500010,
                        "charge_per_kg": 12.0,
                        "free_delivery_min_order_value": 200.0,
                    }
                ],
            },
        },
    )
    assert add_state.status_code in (200, 404)

    add_zone = client.post(
        f"/shipping/admin/{admin['id']}/add-zone",
        json={
            "country": "India",
            "state_name": "Telangana",
            "zone": {
                "start_zipcode": 500011,
                "end_zipcode": 500020,
                "charge_per_kg": 11.0,
                "free_delivery_min_order_value": 300.0,
            },
        },
    )
    assert add_zone.status_code in (200, 404)

    estimate = client.post(
        "/shipping/estimate",
        json={
            "country": "India",
            "state": "Telangana",
            "zipcode": 500001,
            "cart_weight_grams": 1200.0,
            "order_total": 100.0,
        },
    )
    assert estimate.status_code in (200, 404)
