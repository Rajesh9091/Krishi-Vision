"""POST /api/severity. Real pipeline: sampled frames -> vision detect+classify (services.severity)
-> geo -> llm -> tts. Does not touch /api/diagnose (CLAUDE.md rule 2)."""
import json
import time

from fastapi import APIRouter, File, Form, UploadFile

from app.services import llm, severity, tts
from app.services.geo import lookup_zone
from app.settings import settings

router = APIRouter()


def _kb_entry(disease_key: str | None) -> dict | None:
    if disease_key is None:
        return None
    with open(settings.DATA_DIR / "disease_kb.json", encoding="utf-8") as f:
        kb = json.load(f)
    for entry in kb:
        if entry["key"] == disease_key:
            return entry
    return None


def _treatments_block(entry: dict | None) -> str:
    if entry is None:
        return "- No specific treatment on file; advise general care and consulting the local agriculture officer."
    lines = []
    for t in entry["treatments"]:
        lines.append(
            f"- {t['name']} ({t['type']}): {t['dose_per_litre']} per litre of water, "
            f"every {t['interval_days']} days, max {t['max_applications']} times. {t['safety']}"
        )
    return "\n".join(lines)


def _fallback_phrase(result: severity.SeverityResult, kb_entry: dict | None) -> str:
    advice = {
        "low": "Remove and burn the affected leaves, spot-spray only the affected plants, and re-scan in one week.",
        "moderate": "Spray the whole field once with the organic option, and re-scan in five days.",
        "high": "Spray the whole field with the chemical option now, repeat after the interval, and keep workers out until it dries.",
    }[result.severity_level]
    disease_text = result.disease if kb_entry else "an unclear disease"
    return (
        f"About {result.severity_pct} percent of leaves show {disease_text}. "
        f"Severity level: {result.severity_level}. {advice}"
    )


@router.post("/severity")
async def severity_endpoint(
    frames: list[UploadFile] = File(...),
    lat: float | None = Form(None),
    lon: float | None = Form(None),
    lang: str = Form(settings.DEFAULT_LANG),
) -> dict:
    total_start = time.perf_counter()

    vision_start = time.perf_counter()
    frame_bytes = [await f.read() for f in frames]
    result = severity.aggregate(frame_bytes)
    vision_ms = int((time.perf_counter() - vision_start) * 1000)

    zone = lookup_zone(lat, lon)
    kb_entry = _kb_entry(result.disease_key)

    llm_start = time.perf_counter()
    plan_text, used_fallback = llm.generate(
        "severity",
        lang=lang,
        max_sentences=6,
        fallback_text=_fallback_phrase(result, kb_entry),
        crop=result.crop,
        disease=result.disease,
        severity_pct=result.severity_pct,
        severity_level=result.severity_level,
        zone_name=zone.name,
        season=zone.season_note,
        treatments_block=_treatments_block(kb_entry),
    )
    llm_ms = int((time.perf_counter() - llm_start) * 1000)

    tts_start = time.perf_counter()
    tts_result = tts.synthesize(plan_text, lang)
    tts_ms = int((time.perf_counter() - tts_start) * 1000)

    total_ms = int((time.perf_counter() - total_start) * 1000)

    return {
        "severity": {
            "severity_pct": result.severity_pct,
            "severity_level": result.severity_level,
            "crop": result.crop,
            "disease": result.disease,
            "disease_key": result.disease_key,
            "total_boxes": result.total_boxes,
            "infected_boxes": result.infected_boxes,
            "per_frame": result.per_frame,
        },
        "plan_text": plan_text,
        "plan_text_lang": lang,
        "llm_fallback": used_fallback,
        "audio_url": tts_result["audio_url"],
        "tts_fallback": tts_result["tts_fallback"],
        "zone": {"id": zone.id, "name": zone.name, "state": zone.state},
        "timings_ms": {"vision": vision_ms, "llm": llm_ms, "tts": tts_ms, "total": total_ms},
    }
