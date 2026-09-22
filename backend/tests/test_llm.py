from app.services import llm


def test_template_plan_nonempty():
    text = llm.template_plan("tomato_early_blight", "en")
    assert text
    assert "Neem oil" in text or "Mancozeb" in text


def test_generate_falls_back_to_template_when_ollama_down(monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("ollama down")

    monkeypatch.setattr(llm, "_generate_ollama", _boom)
    text, used_fallback = llm.generate(
        "diagnose",
        lang="en",
        crop="Tomato",
        disease="Early blight",
        confidence_pct=91,
        uncertain_note="",
        cause="fungus",
        zone_name="Bengaluru Rural",
        state="Karnataka",
        soil="red loam",
        climate="tropical",
        season="kharif",
        treatments_block="- Neem oil (organic): 5 ml per litre",
        scheme_block="",
        disease_key="tomato_early_blight",
    )
    assert used_fallback is True
    assert text


def test_strip_think():
    assert llm.strip_think("<think>ignore me</think>hello") == "hello"
