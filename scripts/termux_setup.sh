#!/usr/bin/env bash
# Phase 5 step 1: run the Agri-Vision backend + PWA on the iQOO phone itself, inside Termux's
# proot-distro Ubuntu. Run this INSIDE that Ubuntu proot, not in bare Termux (Termux's own
# package set lacks glibc-dependent wheels like torch/onnxruntime).
#
# One-time host setup (run in plain Termux first, not in this script):
#   pkg install proot-distro -y
#   proot-distro install ubuntu
#   proot-distro login ubuntu
# Then, inside the Ubuntu proot shell, copy this repo in (e.g. via `termux-setup-storage` +
# /sdcard, or `git clone` if the phone has network) and run this script from the repo root.
set -euo pipefail

echo "== Agri-Vision Termux/proot-Ubuntu setup (Phase 5 step 1) =="

apt-get update
apt-get install -y python3 python3-venv python3-pip nodejs npm git curl

echo "-- Python backend venv --"
python3 -m venv backend/.venv
backend/.venv/bin/pip install --upgrade pip
backend/.venv/bin/pip install -e backend[dev]

echo "-- Frontend build (static PWA bundle, served by the backend) --"
( cd frontend && npm install && npm run build )

echo "-- Ollama (arm64 Linux binary; run inside this same proot) --"
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh || \
    echo "WARN: Ollama install script failed on this arm64 proot — see docs/phase5_step1_termux.md for the CPU-template fallback."
fi

echo "-- Model weights (same idempotent script as the laptop) --"
PY="$(pwd)/backend/.venv/bin/python" bash scripts/download_models.sh || \
  echo "WARN: some weights failed to fetch on-device — check network/storage, non-fatal for template fallback."

cat <<'EOF'

== Done. To run the on-phone demo ==
  export AGRIVISION_SERVE_FRONTEND=true
  backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000

Then on the phone's own browser, open http://localhost:8000 and "Add to Home Screen" to install
the PWA. See docs/phase5_step1_termux.md for troubleshooting and what still runs on CPU vs NPU.
EOF
