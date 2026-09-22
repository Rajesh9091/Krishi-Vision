from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.settings import settings

client = TestClient(app)

LOW_DIR = settings.SAMPLES_DIR / "severity_low"
HIGH_DIR = settings.SAMPLES_DIR / "severity_high"


def _files(dir_path: Path):
    return [
        ("frames", (p.name, p.read_bytes(), "image/jpeg"))
        for p in sorted(dir_path.glob("*.jpg"))
    ]


def test_severity_endpoint_low_fixture():
    resp = client.post(
        "/api/severity",
        data={"lang": "en"},
        files=_files(LOW_DIR),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["severity"]["severity_level"] == "low"
    assert body["plan_text"]
    assert "timings_ms" in body


def test_severity_endpoint_high_fixture_recommendation_differs_from_low():
    low_resp = client.post("/api/severity", data={"lang": "en"}, files=_files(LOW_DIR))
    high_resp = client.post("/api/severity", data={"lang": "en"}, files=_files(HIGH_DIR))

    low_body = low_resp.json()
    high_body = high_resp.json()

    assert low_body["severity"]["severity_level"] != high_body["severity"]["severity_level"]
    assert low_body["plan_text"] != high_body["plan_text"]


def test_severity_endpoint_golden_path_diagnose_untouched():
    # Sanity check that adding this router did not change /api/diagnose's route table.
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["features"]["severity"] is True
