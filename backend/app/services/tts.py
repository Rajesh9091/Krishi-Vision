"""TTS fallback ladder: MMS-TTS target lang -> MMS-TTS English -> browser speechSynthesis
(signalled via tts_fallback="browser", handled by the frontend)."""
import logging
import re
from uuid import uuid4

import numpy as np
import soundfile as sf

from app.settings import settings

logger = logging.getLogger(__name__)

_models: dict[str, tuple] = {}

_MARKDOWN_RE = re.compile(r"[*_`#]")
_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]"
)
_URL_RE = re.compile(r"https?://\S+")
_BULLET_RE = re.compile(r"^[\s]*[-•·]\s*", re.MULTILINE)
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_SENT_SPLIT_RE = re.compile(r"(?<=[।.?!\n])\s+")

# Only rewrite units when they immediately follow a number, so ordinary words
# containing "g", "l", etc. (e.g. "blight", "litre") are left untouched.
_UNIT_RE = re.compile(r"(?<=\d)\s*(ml|mL|g|kg|L)\b")
_UNIT_WORDS = {"ml": " millilitres", "mL": " millilitres", "g": " grams", "kg": " kilograms", "L": " litres"}
_PERCENT_RE = re.compile(r"(?<=\d)\s*%")


def _replace_unit(match: re.Match) -> str:
    return _UNIT_WORDS[match.group(1)]


def clean_for_tts(text: str) -> str:
    text = _THINK_RE.sub("", text)
    text = _MARKDOWN_RE.sub("", text)
    text = _EMOJI_RE.sub("", text)
    text = _URL_RE.sub("", text)
    text = _BULLET_RE.sub("", text)
    text = _PERCENT_RE.sub(" percent", text)
    text = _UNIT_RE.sub(_replace_unit, text)
    return text.strip()


def _chunk_text(text: str, max_len: int = 250) -> list[str]:
    sentences = [s.strip() for s in _SENT_SPLIT_RE.split(text) if s.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_len:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks or [text[:max_len]]


def _get_model(lang: str):
    if lang not in _models:
        from transformers import VitsModel, AutoTokenizer

        model_name = settings.TTS_MODEL_MAP[lang]
        logger.info("tts: loading %s for lang=%s", model_name, lang)
        model = VitsModel.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        _models[lang] = (model, tokenizer)
    return _models[lang]


def _synthesize_chunk(text: str, lang: str) -> np.ndarray:
    import torch

    model, tokenizer = _get_model(lang)
    inputs = tokenizer(text, return_tensors="pt")
    if inputs["input_ids"].shape[-1] == 0:
        # Text has no characters in this model's script (e.g. LLM answered in the
        # wrong language) -- the VITS model crashes on empty input, so fail fast
        # and let the caller move to the next fallback step instead.
        raise ValueError(f"no {lang} vocabulary tokens found in text: {text[:60]!r}")
    with torch.no_grad():
        output = model(**inputs).waveform
    return output.squeeze().numpy()


def synthesize(text: str, lang: str) -> dict:
    """Returns {"audio_url": str | None, "tts_fallback": "browser" | None}."""
    cleaned = clean_for_tts(text)
    if not cleaned:
        return {"audio_url": None, "tts_fallback": "browser"}

    chunks = _chunk_text(cleaned)

    for try_lang in (lang, "en"):
        if try_lang not in settings.TTS_MODEL_MAP:
            continue
        try:
            sample_rate = None
            pieces: list[np.ndarray] = []
            for chunk in chunks:
                waveform = _synthesize_chunk(chunk, try_lang)
                model, _ = _get_model(try_lang)
                sample_rate = model.config.sampling_rate
                pieces.append(waveform)
                pieces.append(np.zeros(int(sample_rate * 0.25), dtype=waveform.dtype))

            audio = np.concatenate(pieces) if pieces else np.zeros(1, dtype=np.float32)
            peak = np.max(np.abs(audio)) or 1.0
            target_peak = 10 ** (-3 / 20)
            audio = (audio / peak) * target_peak

            audio_16k = _resample_to_16k(audio, sample_rate)

            settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
            audio_name = f"{uuid4()}.wav"
            audio_path = settings.AUDIO_DIR / audio_name
            sf.write(str(audio_path), audio_16k, 16000, subtype="PCM_16")

            return {"audio_url": f"/static/audio/{audio_name}", "tts_fallback": None}
        except Exception:
            logger.exception("tts: synth failed for lang=%s", try_lang)
            continue

    return {"audio_url": None, "tts_fallback": "browser"}


def _resample_to_16k(audio: np.ndarray, sample_rate: int | None) -> np.ndarray:
    if not sample_rate or sample_rate == 16000:
        return audio.astype(np.float32)
    ratio = 16000 / sample_rate
    new_len = int(len(audio) * ratio)
    if new_len <= 0:
        return audio.astype(np.float32)
    x_old = np.linspace(0, 1, num=len(audio))
    x_new = np.linspace(0, 1, num=new_len)
    return np.interp(x_new, x_old, audio).astype(np.float32)
