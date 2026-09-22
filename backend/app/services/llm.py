"""LLM fallback ladder: Ollama qwen3:1.7b -> (llamacpp, not implemented) -> templated plan."""
import json
import logging
import re
from pathlib import Path

import httpx

from app.settings import settings

logger = logging.getLogger(__name__)

LANGUAGE_NAMES = {"kn": "Kannada", "hi": "Hindi", "te": "Telugu", "ta": "Tamil", "en": "English"}

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_prompt_cache: dict[str, str] = {}
_template_cache: dict[str, dict] = {}


def _load_prompt(name: str) -> str:
    if name not in _prompt_cache:
        path = settings.PROMPTS_DIR / f"{name}.txt"
        _prompt_cache[name] = path.read_text(encoding="utf-8").strip()
    return _prompt_cache[name]


def strip_think(text: str) -> str:
    return _THINK_RE.sub("", text).strip()


def generate(
    prompt_name: str,
    lang: str = "en",
    max_sentences: int = 9,
    fallback_text: str | None = None,
    **vars,
) -> tuple[str, bool]:
    """Returns (text, used_fallback). Tries the configured backend, then falls back to
    `fallback_text` if given (a caller-computed deterministic phrasing, e.g. dosage numbers),
    else to the diagnose template plan when a `disease_key` is provided.
    """
    disease_key = vars.get("disease_key")

    def _fallback() -> tuple[str, bool]:
        if fallback_text is not None:
            return fallback_text, True
        if disease_key:
            return template_plan(disease_key, lang), True
        return "", True

    if lang in settings.LLM_UNRELIABLE_LANGS and (fallback_text is not None or disease_key):
        logger.info("llm: %s is a known-unreliable language for this model, using fallback", lang)
        return _fallback()

    language_name = LANGUAGE_NAMES.get(lang, "English")
    system = _load_prompt("system").format(language_name=language_name, max_sentences=max_sentences)
    user = _load_prompt(prompt_name).format(**vars)

    if settings.LLM_BACKEND == "ollama":
        try:
            text = _generate_ollama(system, user)
            return strip_think(text), False
        except Exception:
            logger.exception("llm: ollama generate failed, falling back")

    return _fallback()


def _generate_ollama(system: str, user: str) -> str:
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user + "\n/no_think"},
        ],
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "num_predict": 350,
            "repeat_penalty": 1.1,
        },
    }
    resp = httpx.post(f"{settings.OLLAMA_HOST}/api/chat", json=payload, timeout=60.0)
    resp.raise_for_status()
    data = resp.json()
    content = data.get("message", {}).get("content", "")
    if not content.strip():
        raise RuntimeError("ollama returned empty content")
    return content


def _load_kb_entry(disease_key: str) -> dict:
    with open(settings.DATA_DIR / "disease_kb.json", encoding="utf-8") as f:
        kb = json.load(f)
    for entry in kb:
        if entry["key"] == disease_key:
            return entry
    raise KeyError(disease_key)


def _load_template_frame(lang: str) -> str:
    if lang not in _template_cache:
        path = settings.PROMPTS_DIR / f"templates.{lang}.json"
        if not path.exists():
            path = settings.PROMPTS_DIR / "templates.en.json"
        with open(path, encoding="utf-8") as f:
            _template_cache[lang] = json.load(f)
    return _template_cache[lang]["frame"]


def template_plan(disease_key: str, lang: str) -> str:
    """Fallback ladder step 3 (no LLM at all): compose a plan straight from disease_kb.json."""
    entry = _load_kb_entry(disease_key)
    frame = _load_template_frame(lang)

    organic = next((t for t in entry["treatments"] if t["type"] == "organic"), entry["treatments"][0])
    chemical = next((t for t in entry["treatments"] if t["type"] == "chemical"), entry["treatments"][-1])

    return frame.format(
        crop_local=entry["crop"],
        disease_local=entry["disease"],
        cause_local=entry["cause"],
        organic_name=organic["name"],
        organic_dose=organic["dose_per_litre"],
        organic_interval=organic["interval_days"],
        chemical_name=chemical["name"],
        chemical_dose=chemical["dose_per_litre"],
        chemical_interval=chemical["interval_days"],
        safety_local=chemical["safety"],
        prevention_local=entry["prevention"],
    )
