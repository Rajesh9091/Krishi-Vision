.PHONY: setup dev test demo-check backend-setup frontend-setup seed-db download-models

VENV := backend/.venv
PY := $(VENV)/Scripts/python.exe
PIP := $(VENV)/Scripts/pip.exe

setup: backend-setup frontend-setup download-models seed-db
	@echo "Setup complete. See README.md for manual steps (Ollama, Node)."

backend-setup:
	python -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e backend[dev]

frontend-setup:
	cd frontend && npm install

download-models:
	bash scripts/download_models.sh

seed-db:
	$(PY) backend/app/data/seed_agri_db.py

dev:
	@echo "Starting backend :8000 and frontend :5173 (Ctrl+C stops both)"
	( cd backend && ../$(PY) -m uvicorn app.main:app --reload --port 8000 & )
	cd frontend && npm run dev

test:
	$(PY) -m pytest backend/tests -q
	cd frontend && npm run test -- --run

demo-check:
	$(PY) scripts/demo_check.py
