"""POST /api/diagnose. Real pipeline: vision -> geo/schemes -> llm -> tts."""
import time
import wave
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, UploadFile

from app.services import llm, tts, vision
from app.services.geo import lookup_zone
from app.services.schemes import schemes_for
from app.settings import settings

router = APIRouter()


def _write_stub_wav(path: Path) -> None:
    """Writes a short silent 16kHz mono WAV so demo_check can assert audio exists (stub mode only)."""
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(b"\x00\x00" * 16000)


def _kb_entry(disease_key: str | None) -> dict | None:
    import json

    if disease_key is None:
        return None
    with open(settings.DATA_DIR / "disease_kb.json", encoding="utf-8") as f:
        kb = json.load(f)
    for entry in kb:
        if entry["key"] == disease_key:
            return entry
    return None


def _most_specific_scheme(schemes: list, state: str):
    """Prefer a scheme that applies to fewer states (e.g. a state-specific programme like
    Rythu Bandhu) over a nationwide one like PMFBY, so the zone actually changes the farmer's
    scheme line instead of always surfacing the first nationwide match."""
    import json

    with open(settings.DATA_DIR / "schemes.json", encoding="utf-8") as f:
        all_schemes = {s["id"]: s for s in json.load(f)}

    def specificity(scheme) -> int:
        return len(all_schemes.get(scheme.id, {}).get("states", []))

    return min(schemes, key=specificity)


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


@router.post("/diagnose")
async def diagnose(
    image: UploadFile = File(...),
    lat: float | None = Form(None),
    lon: float | None = Form(None),
    lang: str = Form(settings.DEFAULT_LANG),
    crop_hint: str | None = Form(None),
    stub: bool = False,
) -> dict:
    zone = lookup_zone(lat, lon)
    schemes = schemes_for(zone.state, crop_hint)

    if stub:
        audio_name = f"{uuid4()}.wav"
        audio_path = settings.AUDIO_DIR / audio_name
        settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        _write_stub_wav(audio_path)
        return {
            "diagnosis": {"crop": "Tomato", "disease": "Early blight", "confidence": 0.91},
            "plan_text": "(stub) Spray neem oil, five millilitres per litre of water, every seven days.",
            "plan_text_lang": lang,
            "audio_url": f"/static/audio/{audio_name}",
            "zone": {"id": zone.id, "name": zone.name, "state": zone.state},
            "schemes": [{"id": s.id, "name": s.name, "summary": s.summary} for s in schemes],
            "timings_ms": {"vision": 0, "llm": 0, "tts": 0, "total": 0},
        }

    total_start = time.perf_counter()

    vision_start = time.perf_counter()
    image_bytes = await image.read()
    result = vision.classify_leaf(image_bytes, filename=image.filename or "")
    vision_ms = int((time.perf_counter() - vision_start) * 1000)

    kb_entry = _kb_entry(result.kb_key)
    lang_out = settings.LLM_OUTPUT_LANG_OVERRIDE or lang

    llm_start = time.perf_counter()
    if result.healthy:
        plan_text, used_fallback = llm.generate(
            "diagnose",
            lang=lang_out,
            crop=result.crop,
            disease="Healthy",
            confidence_pct=round(result.confidence * 100),
            uncertain_note="",
            cause="No disease detected",
            zone_name=zone.name,
            state=zone.state,
            soil=zone.soil,
            climate=zone.climate,
            season=zone.season_note,
            treatments_block="- No treatment needed; the plant looks healthy.",
            scheme_block="",
            disease_key=None,
        )
    else:
        uncertain_note = ", which is low, so this is uncertain" if result.uncertain else ""
        scheme_block = ""
        if schemes:
            s = _most_specific_scheme(schemes, zone.state)
            scheme_block = f"Government scheme that may apply: {s.name} — {s.summary}."
        plan_text, used_fallback = llm.generate(
            "diagnose",
            lang=lang_out,
            crop=result.crop,
            disease=result.disease,
            confidence_pct=round(result.confidence * 100),
            uncertain_note=uncertain_note,
            cause=kb_entry["cause"] if kb_entry else "Unknown cause; consult a local expert",
            zone_name=zone.name,
            state=zone.state,
            soil=zone.soil,
            climate=zone.climate,
            season=zone.season_note,
            treatments_block=_treatments_block(kb_entry),
            scheme_block=scheme_block,
            disease_key=result.kb_key,
        )
    llm_ms = int((time.perf_counter() - llm_start) * 1000)

    tts_start = time.perf_counter()
    tts_result = tts.synthesize(plan_text, lang_out)
    tts_ms = int((time.perf_counter() - tts_start) * 1000)

    total_ms = int((time.perf_counter() - total_start) * 1000)

    return {
        "diagnosis": {
            "crop": result.crop,
            "disease": result.disease,
            "confidence": result.confidence,
            "uncertain": result.uncertain,
            "top3": result.top3,
            "disease_key": result.kb_key,
        },
        "plan_text": plan_text,
        "plan_text_lang": lang_out,
        "llm_fallback": used_fallback,
        "audio_url": tts_result["audio_url"],
        "tts_fallback": tts_result["tts_fallback"],
        "zone": {"id": zone.id, "name": zone.name, "state": zone.state},
        "schemes": [{"id": s.id, "name": s.name, "summary": s.summary} for s in schemes],
        "timings_ms": {"vision": vision_ms, "llm": llm_ms, "tts": tts_ms, "total": total_ms},
    }
