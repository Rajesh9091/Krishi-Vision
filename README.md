# Agri-Vision — Offline Crop Pathologist

A fully offline, phone-first crop-disease assistant for rural Indian farmers. A farmer photographs a
leaf, an on-device vision model identifies the disease, a local LLM (Qwen3-1.7B via Ollama) writes a
treatment plan adjusted for the farmer's GPS-derived agro-zone, soil and season, and the plan is spoken
aloud in the farmer's regional language (kn / hi / te / ta / en). Extra features: pesticide dosage from
field size, field-level severity % from a video pan, voice follow-up questions, and offline
government-scheme alerts.

Built for the iQOO Hackathon 2026 (Reskilll) — Track 07 Open Innovation. **Zero cloud calls at
inference time** — every model runs locally.

## Stack

- **Backend**: FastAPI + Python 3.11 (`backend/`)
- **Frontend**: Vite + React 18 + TypeScript + Tailwind (`frontend/`)
- **Vision**: HuggingFace transformers image classifier (PlantVillage) + YOLOv8n for severity scanning
- **LLM**: Qwen3-1.7B via Ollama (`localhost:11434`)
- **TTS**: Meta MMS-TTS (per-language models)
- **ASR**: faster-whisper (voice follow-up)
- **DB**: SQLite (agro-zones, soils, seasons, schemes)

## Quick start

```bash
make setup   # create venv, install backend deps, install frontend deps, seed DB
make dev     # run backend (:8000) + frontend (:5173) together
make test    # backend pytest + frontend vitest
make demo-check   # headless golden-path check; must pass before ending a session
```

## Manual steps (not automated by `make setup`)

- **Ollama**: install from https://ollama.com, then `ollama serve` and `ollama pull qwen3:1.7b`.
- **Node 20+**: install from https://nodejs.org or via `nvm-windows` — required for the frontend.
- Model weights (vision classifier, MMS-TTS, YOLOv8n) are pulled by `scripts/download_models.sh`,
  called from `make setup`. Re-run it any time; it's idempotent.

## Layout

```
backend/    FastAPI app — routers, services (vision/llm/tts/asr/geo/schemes), prompts, data, tests
frontend/   Vite + React + TS UI — capture, diagnosis card, dosage/severity/ask flows
scripts/    download_models.sh, demo_check.py, termux_setup.sh
samples/    sample leaf images + a short pan video for testing
docs/       supporting documentation
```
