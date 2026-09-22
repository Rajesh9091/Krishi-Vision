"""Headless golden-path check. Phase 1: real pipeline (vision -> llm -> tts).
Exit 0 = demo-safe.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.main import app  # noqa: E402
from app.settings import settings  # noqa: E402

STUB_MODE = False  # real pipeline as of Phase 1


def main() -> int:
    sample = next(REPO_ROOT.glob("samples/*early_blight*"), None)
    if sample is None:
        sample = next(REPO_ROOT.glob("samples/*.jpg"), None)
    if sample is None:
        print("FAIL: no sample image found in samples/")
        return 1

    from fastapi.testclient import TestClient

    client = TestClient(app)

    health = client.get("/health")
    if health.status_code != 200:
        print(f"FAIL: /health returned {health.status_code}")
        return 1

    with open(sample, "rb") as f:
        resp = client.post(
            "/api/diagnose",
            params={"stub": "true"} if STUB_MODE else {},
            files={"image": (sample.name, f, "image/jpeg")},
            data={"lang": settings.DEFAULT_LANG},
        )

    if resp.status_code != 200:
        print(f"FAIL: /api/diagnose returned {resp.status_code}: {resp.text}")
        return 1

    body = resp.json()
    audio_url = body.get("audio_url")
    if not audio_url:
        print("FAIL: no audio_url in response")
        return 1

    audio_path = settings.AUDIO_DIR / Path(audio_url).name
    if not audio_path.exists():
        print(f"FAIL: audio file not found at {audio_path}")
        return 1

    print(f"PASS: diagnose -> {body['diagnosis']} audio -> {audio_path.name} (stub_mode={STUB_MODE})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
