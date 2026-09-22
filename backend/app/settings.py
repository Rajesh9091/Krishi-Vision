"""All feature flags and model names live here. Nothing else should hardcode them."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # --- backends / fallback ladder (CLAUDE.md §5) ---
    LLM_BACKEND: str = "ollama"  # ollama | llamacpp | template
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:1.7b"
    LLM_OUTPUT_LANG_OVERRIDE: str | None = None  # e.g. "en" if a language reads poorly

    # Languages where qwen3:1.7b was observed (Phase 1 rehearsal) to answer in the wrong
    # script/language, loop nonsensically, or hallucinate away from the given facts --
    # see progress.md decisions log. For these, skip the LLM entirely and use the
    # hand-written, TTS-safe template plan instead. English rehearsed reliably and stays live.
    LLM_UNRELIABLE_LANGS: list[str] = ["kn", "hi", "te", "ta"]

    VISION_MODEL: str = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
    VISION_CONFIDENCE_THRESHOLD: float = 0.45

    YOLO_MODEL: str = "yolov8n.pt"

    TTS_MODEL_MAP: dict[str, str] = {
        "kn": "facebook/mms-tts-kan",
        "hi": "facebook/mms-tts-hin",
        "te": "facebook/mms-tts-tel",
        "ta": "facebook/mms-tts-tam",
        "en": "facebook/mms-tts-eng",
    }

    ASR_MODEL: str = "small"  # faster-whisper size

    DEFAULT_LANG: str = "kn"
    DEFAULT_ZONE_ID: str = "bengaluru_rural"

    # --- feature flags (default OFF unless a phase turns them on) ---
    ENABLE_DOSAGE: bool = True
    ENABLE_SEVERITY: bool = True
    ENABLE_ASK: bool = True

    # Phase 5 step 1: when True, the backend also serves the built frontend (frontend/dist) at "/",
    # so one process on the phone (Termux) is the whole app. Default OFF — the laptop dev workflow
    # (separate `npm run dev` + Vite proxy) is unaffected either way.
    SERVE_FRONTEND: bool = False

    # --- paths ---
    DATA_DIR: Path = APP_DIR / "data"
    DB_PATH: Path = APP_DIR / "data" / "agri.db"
    PROMPTS_DIR: Path = APP_DIR / "prompts"
    AUDIO_DIR: Path = APP_DIR / "static" / "audio"
    SAMPLES_DIR: Path = APP_DIR.parent.parent / "samples"

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_prefix="AGRIVISION_")


settings = Settings()
