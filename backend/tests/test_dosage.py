import math

import pytest

from app.services import dosage


def test_to_acres_acre_is_identity():
    assert dosage.to_acres(2, "acre") == 2


def test_to_acres_hectare():
    assert dosage.to_acres(1, "hectare") == pytest.approx(2.471)


def test_to_acres_gunta():
    assert dosage.to_acres(40, "gunta") == pytest.approx(1.0)


def test_to_acres_unknown_unit_raises():
    with pytest.raises(ValueError):
        dosage.to_acres(1, "bigha")


def test_compute_tomato_early_blight_organic_two_acres():
    numbers = dosage.compute("tomato_early_blight", 2, "acre", "organic")

    assert numbers["treatment_name"] == "Neem oil"
    assert numbers["treatment_type"] == "organic"
    # water_litres_per_acre = 200, area = 2 acres
    assert numbers["water_litres"] == pytest.approx(400)
    # dose_per_litre = 5 ml -> 5 * 400 = 2000 ml total
    assert numbers["product_amount"] == pytest.approx(2000)
    assert numbers["product_unit"] == "ml"
    # 15 L tank * 5 ml/L = 75 ml per tank
    assert numbers["per_tank_amount"] == pytest.approx(75)
    assert numbers["tank_fills"] == math.ceil(400 / 15)
    assert numbers["interval_days"] == 7
    assert numbers["max_applications"] == 4


def test_compute_tomato_early_blight_chemical_two_acres():
    numbers = dosage.compute("tomato_early_blight", 2, "acre", "chemical")

    assert numbers["treatment_name"] == "Mancozeb"
    assert numbers["treatment_type"] == "chemical"
    assert numbers["product_unit"] == "g"


def test_compute_rescales_correctly_for_hectare():
    acre_numbers = dosage.compute("tomato_early_blight", 2.471, "acre", "organic")
    hectare_numbers = dosage.compute("tomato_early_blight", 1, "hectare", "organic")

    assert hectare_numbers["water_litres"] == pytest.approx(acre_numbers["water_litres"], rel=1e-3)
    assert hectare_numbers["product_amount"] == pytest.approx(acre_numbers["product_amount"], rel=1e-3)


def test_compute_gunta_small_area():
    numbers = dosage.compute("tomato_early_blight", 10, "gunta", "organic")

    # 10 gunta = 0.25 acre -> water = 200 * 0.25 = 50 L
    assert numbers["water_litres"] == pytest.approx(50)
    assert numbers["tank_fills"] == math.ceil(50 / 15)


def test_compute_unknown_disease_raises():
    with pytest.raises(KeyError):
        dosage.compute("not_a_real_disease", 1, "acre", "organic")


def test_compute_any_pref_defaults_to_first_treatment():
    numbers = dosage.compute("tomato_early_blight", 1, "acre", "any")
    assert numbers["treatment_name"] == "Neem oil"
