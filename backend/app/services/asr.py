"""ASR: faster-whisper `small`, loaded lazily and cached. Fallback ladder step: if the model
fails to load or the transcript is empty/too short, the caller (routers/ask.py) falls back to
the text field the frontend also sends -- so a farmer who can't be heard can still type."""
import logging

from app.settings import settings

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        logger.info("asr: loading faster-whisper %s", settings.ASR_MODEL)
        _model = WhisperModel(settings.ASR_MODEL, device="cpu", compute_type="int8")
    return _model


def transcribe(audio_path: str, lang: str) -> dict:
    """Returns {"text": str, "error": "could_not_hear" | None}."""
    try:
        model = _get_model()
        segments, _info = model.transcribe(
            audio_path, language=lang, beam_size=1, vad_filter=True
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
    except Exception:
        logger.exception("asr: transcribe failed")
        return {"text": "", "error": "could_not_hear"}

    if len(text) < 3:
        return {"text": "", "error": "could_not_hear"}
    return {"text": text, "error": None}
