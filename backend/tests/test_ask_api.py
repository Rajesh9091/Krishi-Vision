from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ask_endpoint_text_question_returns_answer():
    resp = client.post(
        "/api/ask",
        data={
            "text": "How often do I spray?",
            "lang": "en",
            "context": '{"crop": "Tomato", "disease": "Early blight", '
            '"severity_or_confidence": "99 percent confidence", '
            '"treatment_summary": "Neem oil every seven days"}',
            "history": "[]",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["question"] == "How often do I spray?"
    assert body["answer"]
    assert "timings_ms" in body


def test_ask_endpoint_no_text_no_audio_returns_could_not_hear():
    resp = client.post("/api/ask", data={"lang": "en"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["asr_error"] == "could_not_hear"
    assert body["answer"] == ""


def test_ask_endpoint_unreliable_lang_uses_deterministic_fallback():
    resp = client.post(
        "/api/ask",
        data={
            "text": "When should I spray again?",
            "lang": "kn",
            "context": '{"crop": "Tomato", "disease": "Early blight", '
            '"treatment_summary": "Neem oil every seven days"}',
            "history": "[]",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["llm_fallback"] is True
    assert body["answer"]
