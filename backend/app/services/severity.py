"""Field-level severity: sample frames from a scan, detect leaf/plant boxes in each
(vision.detect_leaves), classify every box (vision.classify_image), and aggregate the
infected/total ratio across the whole scan. No LLM arithmetic -- percentages are counted here;
prompts/severity.txt only phrases the result (same pattern as services/dosage.py)."""
import logging
from collections import Counter
from dataclasses import dataclass, field
from io import BytesIO

from PIL import Image

from app.services import vision

logger = logging.getLogger(__name__)

MAX_FRAMES = 10
LOW_MAX_PCT = 15.0
MODERATE_MAX_PCT = 40.0


@dataclass
class SeverityResult:
    severity_pct: float
    severity_level: str  # low | moderate | high
    crop: str
    disease: str
    disease_key: str | None
    total_boxes: int
    infected_boxes: int
    per_frame: list[dict] = field(default_factory=list)


def severity_level(pct: float) -> str:
    if pct < LOW_MAX_PCT:
        return "low"
    if pct <= MODERATE_MAX_PCT:
        return "moderate"
    return "high"


def sample_frames(frames: list[bytes], max_frames: int = MAX_FRAMES) -> list[bytes]:
    """Evenly samples at most `max_frames` from the submitted clip's frames, keeping order."""
    if len(frames) <= max_frames:
        return frames
    step = len(frames) / max_frames
    return [frames[int(i * step)] for i in range(max_frames)]


def aggregate(frames: list[bytes]) -> SeverityResult:
    """Detects leaf boxes per sampled frame, classifies each, and returns the infected-ratio
    severity plus the majority disease among infected boxes."""
    sampled = sample_frames(frames)

    total_boxes = 0
    infected_boxes = 0
    disease_counts: Counter[tuple[str, str, str | None]] = Counter()
    per_frame: list[dict] = []

    for raw in sampled:
        try:
            image = Image.open(BytesIO(raw)).convert("RGB")
        except Exception:
            logger.exception("severity: could not decode a frame, skipping it")
            continue

        boxes = vision.detect_leaves(image)
        frame_total = 0
        frame_infected = 0
        for box_image in boxes:
            try:
                diag = vision.classify_image(box_image)
            except Exception:
                logger.exception("severity: classifying a box failed, skipping it")
                continue
            frame_total += 1
            if not diag.healthy:
                frame_infected += 1
                disease_counts[(diag.crop, diag.disease, diag.kb_key)] += 1

        total_boxes += frame_total
        infected_boxes += frame_infected
        per_frame.append({"boxes": frame_total, "infected": frame_infected})

    pct = round(100 * infected_boxes / total_boxes, 1) if total_boxes else 0.0
    level = severity_level(pct)

    if disease_counts:
        (crop, disease, disease_key), _ = disease_counts.most_common(1)[0]
    else:
        crop, disease, disease_key = "Unknown", "Healthy", None

    return SeverityResult(
        severity_pct=pct,
        severity_level=level,
        crop=crop,
        disease=disease,
        disease_key=disease_key,
        total_boxes=total_boxes,
        infected_boxes=infected_boxes,
        per_frame=per_frame,
    )
