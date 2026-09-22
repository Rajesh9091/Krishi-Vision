"""Pure arithmetic for pesticide/water dosage. The LLM only phrases these numbers in
prompts/dosage.txt -- it never calculates anything (see CLAUDE.md decisions log)."""
import json
import math
import re

from app.settings import settings

ACRE_PER_HECTARE = 2.471
ACRE_PER_GUNTA = 0.025
KNAPSACK_TANK_LITRES = 15

_DOSE_RE = re.compile(r"^([\d.]+)\s*(\w+)$")


def to_acres(value: float, unit: str) -> float:
    if unit == "acre":
        return value
    if unit == "hectare":
        return value * ACRE_PER_HECTARE
    if unit == "gunta":
        return value * ACRE_PER_GUNTA
    raise ValueError(f"unknown area unit: {unit!r}")


def _load_kb_entry(disease_key: str) -> dict:
    with open(settings.DATA_DIR / "disease_kb.json", encoding="utf-8") as f:
        kb = json.load(f)
    for entry in kb:
        if entry["key"] == disease_key:
            return entry
    raise KeyError(disease_key)


def _pick_treatment(entry: dict, pref: str) -> dict:
    treatments = entry["treatments"]
    if pref == "organic":
        return next((t for t in treatments if t["type"] == "organic"), treatments[0])
    if pref == "chemical":
        return next((t for t in treatments if t["type"] == "chemical"), treatments[-1])
    return treatments[0]


def _parse_dose(dose_per_litre: str) -> tuple[float, str]:
    match = _DOSE_RE.match(dose_per_litre.strip())
    if not match:
        raise ValueError(f"cannot parse dose_per_litre: {dose_per_litre!r}")
    return float(match.group(1)), match.group(2)


def compute(disease_key: str, area_value: float, area_unit: str, treatment_pref: str = "any") -> dict:
    """Returns every number the farmer needs: total water, total product, per-tank amount for
    a 15 L knapsack sprayer, tank fills, spray interval and safety line."""
    entry = _load_kb_entry(disease_key)
    treatment = _pick_treatment(entry, treatment_pref)
    dose_value, dose_unit = _parse_dose(treatment["dose_per_litre"])

    area_acres = to_acres(area_value, area_unit)
    water_litres = round(treatment["water_litres_per_acre"] * area_acres, 1)
    tank_fills = max(1, math.ceil(water_litres / KNAPSACK_TANK_LITRES))
    per_tank_amount = round(dose_value * KNAPSACK_TANK_LITRES, 2)
    product_amount = round(dose_value * water_litres, 2)

    return {
        "crop": entry["crop"],
        "disease": entry["disease"],
        "treatment_name": treatment["name"],
        "treatment_type": treatment["type"],
        "area_value": area_value,
        "area_unit": area_unit,
        "area_acres": round(area_acres, 3),
        "water_litres": water_litres,
        "product_amount": product_amount,
        "product_unit": dose_unit,
        "per_tank_amount": per_tank_amount,
        "tank_fills": tank_fills,
        "interval_days": treatment["interval_days"],
        "max_applications": treatment["max_applications"],
        "safety": treatment["safety"],
    }
