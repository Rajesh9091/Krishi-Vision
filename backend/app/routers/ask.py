"""POST /api/ask. Voice or text follow-up question, answered from the earlier diagnosis
context the frontend sends back (server is stateless -- CLAUDE.md rule: no new hidden state)."""
import json
import tempfile
import time
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from app.services import asr, llm, tts
from app.settings import settings

router = APIRouter()


def _history_block(history: list[dict]) -> str:
    if not history:
        return "(none yet)"
    lines = []
    for turn in history[-3:]:
        lines.append(f"Farmer: {turn.get('question', '')}")
        lines.append(f"You: {turn.get('answer', '')}")
    return "\n".join(lines)


@router.post("/ask")
async def ask_endpoint(
    audio: UploadFile | None = File(None),
    text: str | None = Form(None),
    context: str = Form("{}"),
    history: str = Form("[]"),
    lang: str = Form(settings.DEFAULT_LANG),
) -> dict:
    total_start = time.perf_counter()

    ctx = json.loads(context) if context else {}
    past_turns = json.loads(history) if history else []

    asr_start = time.perf_counter()
    question = (text or "").strip()
    asr_error = None
    if not question and audio is not None:
        audio_bytes = await audio.read()
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            result = asr.transcribe(tmp_path, lang)
            question = result["text"]
            asr_error = result["error"]
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    asr_ms = int((time.perf_counter() - asr_start) * 1000)

    if not question:
        return {
            "question": "",
            "answer": "",
            "asr_error": asr_error or "could_not_hear",
            "audio_url": None,
            "tts_fallback": "browser",
            "timings_ms": {"asr": asr_ms, "llm": 0, "tts": 0, "total": asr_ms},
        }

    llm_start = time.perf_counter()
    severity_or_confidence = ctx.get("severity_or_confidence", "an unclear result")
    treatment_summary = ctx.get("treatment_summary", "no treatment discussed yet")
    dosage_summary = ctx.get("dosage_summary", "")
    answer, used_fallback = llm.generate(
        "followup",
        lang=lang,
        max_sentences=4,
        fallback_text=(
            f"For {ctx.get('crop', 'your crop')} with {ctx.get('disease', 'this issue')}, "
            f"follow the treatment already discussed: {treatment_summary}. "
            "Please ask your village agriculture officer for anything beyond this."
        ),
        crop=ctx.get("crop", "the crop"),
        disease=ctx.get("disease", "the disease"),
        severity_or_confidence=severity_or_confidence,
        treatment_summary=treatment_summary,
        dosage_summary_or_empty=dosage_summary,
        history_block=_history_block(past_turns),
        question=question,
    )
    llm_ms = int((time.perf_counter() - llm_start) * 1000)

    tts_start = time.perf_counter()
    tts_result = tts.synthesize(answer, lang)
    tts_ms = int((time.perf_counter() - tts_start) * 1000)

    total_ms = int((time.perf_counter() - total_start) * 1000)

    return {
        "question": question,
        "answer": answer,
        "asr_error": None,
        "llm_fallback": used_fallback,
        "audio_url": tts_result["audio_url"],
        "tts_fallback": tts_result["tts_fallback"],
        "timings_ms": {"asr": asr_ms, "llm": llm_ms, "tts": tts_ms, "total": total_ms},
    }
