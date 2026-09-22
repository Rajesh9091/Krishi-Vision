from app.services.schemes import schemes_for


def test_schemes_for_karnataka():
    schemes = schemes_for("Karnataka")
    ids = {s.id for s in schemes}
    assert "pmfby" in ids
    assert "pm_kisan" in ids
    assert "raitha_siri" in ids


def test_schemes_for_telangana_tomato():
    schemes = schemes_for("Telangana", "Tomato")
    ids = {s.id for s in schemes}
    assert "rythu_bandhu" in ids


def test_schemes_for_unknown_state_empty():
    schemes = schemes_for("Nowhere")
    assert schemes == []
