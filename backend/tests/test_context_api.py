from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_context_bengaluru_has_zone_and_scheme():
    resp = client.get("/api/context", params={"lat": 12.97, "lon": 77.59})
    assert resp.status_code == 200
    body = resp.json()
    assert body["zone"]["name"] == "Bengaluru Rural"
    assert len(body["schemes"]) >= 1
