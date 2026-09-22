"""Vision fallback ladder step 1: HF PlantVillage classifier -> label map -> KB lookup."""
import json
import logging
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

from PIL import Image

from app.settings import settings

logger = logging.getLogger(__name__)

_disease_kb: list[dict] | None = None
_classifier = None

# The checkpoint's labels are human-readable (e.g. "Tomato with Early Blight"), not the
# PlantVillage folder-name format our disease_kb.json keys on. Map them explicitly.
_LABEL_TO_KB_KEY = {
    "Apple Scab": "apple_scab",
    "Potato with Early Blight": "potato_early_blight",
    "Potato with Late Blight": "potato_late_blight",
    "Bell Pepper with Bacterial Spot": "pepper_bacterial_spot",
    "Corn (Maize) with Northern Leaf Blight": "corn_leaf_blight",
    "Corn (Maize) with Common Rust": "corn_common_rust",
    "Grape with Black Rot": "grape_black_rot",
    "Tomato with Bacterial Spot": "tomato_bacterial_spot",
    "Tomato with Early Blight": "tomato_early_blight",
    "Tomato with Late Blight": "tomato_late_blight",
    "Tomato with Leaf Mold": "tomato_leaf_mold",
    "Tomato with Septoria Leaf Spot": "tomato_septoria_leaf_spot",
    "Tomato Yellow Leaf Curl Virus": "tomato_yellow_leaf_curl_virus",
    "Tomato Mosaic Virus": "tomato_mosaic_virus",
}

_HEALTHY_PREFIXES = ("Healthy ",)


@dataclass
class Diagnosis:
    crop: str
    disease: str
    confidence: float
    healthy: bool
    kb_key: str | None
    top3: list[dict] = field(default_factory=list)
    uncertain: bool = False


def _load_kb() -> list[dict]:
    global _disease_kb
    if _disease_kb is None:
        with open(settings.DATA_DIR / "disease_kb.json", encoding="utf-8") as f:
            _disease_kb = json.load(f)
    return _disease_kb


def _kb_entry_for_key(kb_key: str | None) -> dict | None:
    if kb_key is None:
        return None
    for entry in _load_kb():
        if entry["key"] == kb_key:
            return entry
    return None


def _crop_from_label(label: str) -> str:
    for prefix in _HEALTHY_PREFIXES:
        if label.startswith(prefix):
            return label[len(prefix):].replace(" Plant", "").strip()
    for sep in (" with ", " Yellow Leaf Curl Virus", " Mosaic Virus"):
        if sep in label:
            return label.split(sep)[0].strip()
    return label.split()[0]


def _interpret_label(label: str) -> tuple[str, str, bool, str | None]:
    """label -> (crop, disease, healthy, kb_key)"""
    healthy = label.startswith(_HEALTHY_PREFIXES) or label == "Healthy"
    crop = _crop_from_label(label)
    if healthy:
        return crop, "Healthy", True, None
    kb_key = _LABEL_TO_KB_KEY.get(label)
    entry = _kb_entry_for_key(kb_key)
    disease = entry["disease"] if entry else label
    crop = entry["crop"] if entry else crop
    return crop, disease, False, kb_key


def _get_classifier():
    global _classifier
    if _classifier is None:
        from transformers import AutoModelForImageClassification, MobileNetV2ImageProcessor

        logger.info("vision: loading %s", settings.VISION_MODEL)
        processor = MobileNetV2ImageProcessor.from_pretrained(settings.VISION_MODEL)
        model = AutoModelForImageClassification.from_pretrained(settings.VISION_MODEL)
        model.eval()
        _classifier = (model, processor)
    return _classifier


def _keyword_fallback(filename: str) -> Diagnosis:
    """Fallback ladder step 2 (dev only): match sample filename against disease_kb keys."""
    stem = Path(filename).stem.lower()
    for entry in _load_kb():
        if entry["key"] in stem or stem in entry["key"]:
            return Diagnosis(
                crop=entry["crop"],
                disease=entry["disease"],
                confidence=0.5,
                healthy=False,
                kb_key=entry["key"],
                top3=[{"label": entry["raw_label"], "score": 0.5}],
            )
    return Diagnosis(
        crop="Unknown", disease="Uncertain", confidence=0.0,
        healthy=False, kb_key=None, top3=[], uncertain=True,
    )


def classify_image(image: Image.Image) -> Diagnosis:
    """Runs the PlantVillage classifier on an already-loaded image. Raises on failure --
    callers decide the fallback (keyword match for a single upload, skip for a severity crop)."""
    import torch

    model, processor = _get_classifier()
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.nn.functional.softmax(logits, dim=-1)[0]
    top_probs, top_idx = torch.topk(probs, k=min(3, probs.shape[0]))
    results = [
        {"label": model.config.id2label[int(idx)], "score": float(score)}
        for score, idx in zip(top_probs, top_idx)
    ]

    top = results[0]
    confidence = top["score"]
    crop, disease, healthy, kb_key = _interpret_label(top["label"])

    uncertain = confidence < settings.VISION_CONFIDENCE_THRESHOLD
    if uncertain and not healthy:
        disease = "Uncertain"

    return Diagnosis(
        crop=crop,
        disease=disease,
        confidence=confidence,
        healthy=healthy,
        kb_key=kb_key,
        top3=results,
        uncertain=uncertain,
    )


def classify_leaf(image_bytes: bytes, filename: str = "") -> Diagnosis:
    """Fallback ladder step 3: any classifier failure still returns an 'Uncertain' diagnosis."""
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        return classify_image(image)
    except Exception:
        logger.exception("vision: classifier failed, falling back to keyword match")
        return _keyword_fallback(filename)


_yolo_model = None
_POTTED_PLANT_CLASS = 58  # COCO class id; nearest stand-in for "leafy plant" (see CLAUDE.md §4)


def _get_yolo():
    global _yolo_model
    if _yolo_model is None:
        from ultralytics import YOLO

        logger.info("vision: loading YOLO %s", settings.YOLO_MODEL)
        _yolo_model = YOLO(settings.YOLO_MODEL)
    return _yolo_model


def _tile_grid(image: Image.Image, grid: int = 3) -> list[Image.Image]:
    """Fallback when YOLO finds no plant box -- reliable for close-up field-row footage where
    the plant fills the frame and there is no distinct 'potted plant' object to detect."""
    w, h = image.size
    tiles = []
    for row in range(grid):
        for col in range(grid):
            box = (col * w // grid, row * h // grid, (col + 1) * w // grid, (row + 1) * h // grid)
            tiles.append(image.crop(box))
    return tiles


def detect_leaves(image: Image.Image) -> list[Image.Image]:
    """Returns cropped regions likely to contain a leaf/plant: YOLOv8n 'potted plant' boxes,
    falling back to a 3x3 tile grid when YOLO finds nothing (or fails to load)."""
    try:
        model = _get_yolo()
        result = model.predict(image, verbose=False)[0]
        boxes = []
        for box in result.boxes:
            if int(box.cls[0]) == _POTTED_PLANT_CLASS:
                x1, y1, x2, y2 = (int(v) for v in box.xyxy[0])
                if x2 > x1 and y2 > y1:
                    boxes.append(image.crop((x1, y1, x2, y2)))
        if boxes:
            return boxes
    except Exception:
        logger.exception("vision: YOLO detect failed, falling back to tiling")

    return _tile_grid(image)
