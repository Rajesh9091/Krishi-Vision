from pathlib import Path

from app.services import severity, vision
from app.settings import settings

LOW_DIR = settings.SAMPLES_DIR / "severity_low"
HIGH_DIR = settings.SAMPLES_DIR / "severity_high"


def _load(dir_path: Path) -> list[bytes]:
    return [p.read_bytes() for p in sorted(dir_path.glob("*.jpg"))]


def test_detect_leaves_returns_at_least_one_box_via_tiling_fallback():
    from io import BytesIO

    from PIL import Image

    image = Image.new("RGB", (300, 300), color=(0, 120, 0))
    boxes = vision.detect_leaves(image)
    assert len(boxes) >= 1


def test_low_severity_fixture_scores_low():
    frames = _load(LOW_DIR)
    assert frames, "samples/severity_low fixtures missing"
    result = severity.aggregate(frames)
    assert result.severity_level == "low"
    assert result.severity_pct < severity.LOW_MAX_PCT


def test_high_severity_fixture_scores_moderate_or_high():
    frames = _load(HIGH_DIR)
    assert frames, "samples/severity_high fixtures missing"
    result = severity.aggregate(frames)
    assert result.severity_level in ("moderate", "high")
    assert result.severity_pct > 0


def test_recommendation_differs_between_low_and_high_severity():
    low_result = severity.aggregate(_load(LOW_DIR))
    high_result = severity.aggregate(_load(HIGH_DIR))
    assert low_result.severity_level != high_result.severity_level
    assert low_result.severity_pct < high_result.severity_pct


def test_severity_level_thresholds():
    assert severity.severity_level(0) == "low"
    assert severity.severity_level(14.9) == "low"
    assert severity.severity_level(15) == "moderate"
    assert severity.severity_level(40) == "moderate"
    assert severity.severity_level(40.1) == "high"


def test_sample_frames_caps_at_max_and_keeps_order():
    frames = [str(i).encode() for i in range(23)]
    sampled = severity.sample_frames(frames, max_frames=10)
    assert len(sampled) == 10
    indices = [int(f.decode()) for f in sampled]
    assert indices == sorted(indices)


def test_aggregate_empty_frames_returns_zero_percent():
    result = severity.aggregate([])
    assert result.severity_pct == 0.0
    assert result.severity_level == "low"
