#!/usr/bin/env bash
# Idempotent model download. Safe to re-run. Zero cloud inference — this only fetches weights.
set -euo pipefail

PY="${PY:-python}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== Agri-Vision model download =="

echo "-- Vision classifier (HF): linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification --"
"$PY" - <<'PYEOF'
from transformers import AutoImageProcessor, AutoModelForImageClassification
name = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
try:
    AutoImageProcessor.from_pretrained(name)
    AutoModelForImageClassification.from_pretrained(name)
    print(f"OK: {name} cached")
except Exception as e:
    print(f"WARN: could not fetch {name}: {e}")
    print("Vision fallback (keyword match on filename) will be used until this is resolved.")
PYEOF

echo "-- MMS-TTS models (kn, hi, te, ta, en) --"
"$PY" - <<'PYEOF'
from transformers import VitsModel, AutoTokenizer
langs = {"kn": "kan", "hi": "hin", "te": "tel", "ta": "tam", "en": "eng"}
for code, suffix in langs.items():
    name = f"facebook/mms-tts-{suffix}"
    try:
        VitsModel.from_pretrained(name)
        AutoTokenizer.from_pretrained(name)
        print(f"OK: {name} cached")
    except Exception as e:
        print(f"WARN: could not fetch {name}: {e}")
PYEOF

echo "-- YOLOv8n (COCO weights, for Phase 3 leaf detection) --"
"$PY" - <<'PYEOF'
try:
    from ultralytics import YOLO
    YOLO("yolov8n.pt")
    print("OK: yolov8n.pt cached")
except Exception as e:
    print(f"WARN: could not fetch yolov8n.pt: {e}")
PYEOF

echo "-- faster-whisper ASR (small) --"
"$PY" - <<'PYEOF'
try:
    from faster_whisper import WhisperModel
    WhisperModel("small", device="cpu", compute_type="int8")
    print("OK: faster-whisper small cached")
except Exception as e:
    print(f"WARN: could not fetch faster-whisper small: {e}")
    print("ASR will fail closed; AskBar falls back to its text input.")
PYEOF

echo "-- Ollama / Qwen3-1.7B check --"
if command -v ollama >/dev/null 2>&1; then
    if ollama list 2>/dev/null | grep -q "qwen3:1.7b"; then
        echo "OK: ollama has qwen3:1.7b"
    else
        echo "MISSING: run 'ollama pull qwen3:1.7b' (~1.1 GB) before Phase 1."
    fi
else
    echo "MISSING: ollama is not installed. Install from https://ollama.com, then run:"
    echo "  ollama serve"
    echo "  ollama pull qwen3:1.7b"
fi

echo "== Done. Warnings above are non-fatal for Phase 0 (stub mode). =="
