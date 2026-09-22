"""POST /api/dosage. Numbers are computed in app.services.dosage; the LLM (or its deterministic
fallback) only phrases them in the farmer's language -- it never calculates anything."""
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import dosage, llm, tts
from app.settings import settings

router = APIRouter()


class DosageRequest(BaseModel):
    disease_key: str
    area_value: float
    area_unit: str = "acre"  # acre | hectare | gunta
    lang: str = settings.DEFAULT_LANG
    treatment_pref: str = "any"  # organic | chemical | any


def _fallback_phrase(numbers: dict) -> str:
    return (
        f"For {numbers['area_value']} {numbers['area_unit']} of {numbers['crop']} with "
        f"{numbers['disease']}, use {numbers['treatment_name']}. Total water needed: "
        f"{numbers['water_litres']} litres. Total {numbers['treatment_name']} needed: "
        f"{numbers['product_amount']} {numbers['product_unit']}. Per fifteen litre knapsack tank: "
        f"{numbers['per_tank_amount']} {numbers['product_unit']}. Number of tank fills: "
        f"{numbers['tank_fills']}. Spray every {numbers['interval_days']} days, at most "
        f"{numbers['max_applications']} times. {numbers['safety']}"
    )


@router.post("/dosage")
async def dosage_endpoint(req: DosageRequest) -> dict:
    total_start = time.perf_counter()

    try:
        numbers = dosage.compute(req.disease_key, req.area_value, req.area_unit, req.treatment_pref)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown disease_key")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    llm_start = time.perf_counter()
    plan_text, used_fallback = llm.generate(
        "dosage",
        lang=req.lang,
        max_sentences=7,
        fallback_text=_fallback_phrase(numbers),
        area_value=numbers["area_value"],
        area_unit=numbers["area_unit"],
        crop=numbers["crop"],
        disease=numbers["disease"],
        treatment_name=numbers["treatment_name"],
        treatment_type=numbers["treatment_type"],
        water_litres=numbers["water_litres"],
        product_amount=numbers["product_amount"],
        product_unit=numbers["product_unit"],
        per_tank_amount=numbers["per_tank_amount"],
        tank_fills=numbers["tank_fills"],
        interval_days=numbers["interval_days"],
        max_applications=numbers["max_applications"],
        safety=numbers["safety"],
    )
    llm_ms = int((time.perf_counter() - llm_start) * 1000)

    tts_start = time.perf_counter()
    tts_result = tts.synthesize(plan_text, req.lang)
    tts_ms = int((time.perf_counter() - tts_start) * 1000)

    total_ms = int((time.perf_counter() - total_start) * 1000)

    return {
        "numbers": numbers,
        "plan_text": plan_text,
        "plan_text_lang": req.lang,
        "llm_fallback": used_fallback,
        "audio_url": tts_result["audio_url"],
        "tts_fallback": tts_result["tts_fallback"],
        "timings_ms": {"llm": llm_ms, "tts": tts_ms, "total": total_ms},
    }
