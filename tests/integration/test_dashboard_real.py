def test_dashboard_real(client):
    response = client.get("/dashboard/overview")
    assert response.status_code == 200
