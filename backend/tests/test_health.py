def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["database"] == "ok"


def test_ui_home_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Universal File Comparer" in resp.text
