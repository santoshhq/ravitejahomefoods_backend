def test_health_real(client):
    response = client.get("/")
    assert response.status_code == 200
