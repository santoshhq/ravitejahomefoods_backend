def test_dashboard_overview(client):
    response = client.get("/dashboard/overview")
    assert response.status_code == 200
    data = response.json()
    assert data.get("total")
    assert data.get("daily")
