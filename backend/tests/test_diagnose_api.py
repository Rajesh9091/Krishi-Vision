from fastapi.testclient import TestClient

from app.main import app
from app.settings import settings

client = TestClient(app)


def test_diagnose_e2e_returns_200_with_audio_and_timings():
    sample = settings.SAMPLES_DIR / "tomato_early_blight.jpg"
    with open(sample, "rb") as f:
        resp = client.post(
            "/api/diagnose",
            files={"image": (sample.name, f, "image/jpeg")},
            data={"lang": "en", "lat": "12.97", "lon": "77.59"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["diagnosis"]["crop"]
    assert body["plan_text"]
    assert "timings_ms" in body
    assert set(body["timings_ms"]) == {"vision", "llm", "tts", "total"}
