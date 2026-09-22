from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dosage_endpoint_returns_numbers_and_plan():
    resp = client.post(
        "/api/dosage",
        json={
            "disease_key": "tomato_early_blight",
            "area_value": 2,
            "area_unit": "acre",
            "lang": "en",
            "treatment_pref": "organic",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["numbers"]["treatment_name"] == "Neem oil"
    assert body["numbers"]["water_litres"] == 400
    assert body["plan_text"]
    assert "timings_ms" in body


def test_dosage_endpoint_unreliable_lang_uses_deterministic_fallback():
    resp = client.post(
        "/api/dosage",
        json={
            "disease_key": "tomato_early_blight",
            "area_value": 1,
            "area_unit": "hectare",
            "lang": "kn",
            "treatment_pref": "chemical",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["llm_fallback"] is True
    assert body["numbers"]["treatment_name"] == "Mancozeb"


def test_dosage_endpoint_unknown_disease_key_returns_error():
    resp = client.post(
        "/api/dosage",
        json={"disease_key": "not_real", "area_value": 1, "area_unit": "acre"},
    )
    assert resp.status_code >= 400
