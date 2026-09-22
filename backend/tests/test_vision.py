from pathlib import Path

from app.services.vision import classify_leaf
from app.settings import settings

SAMPLES = settings.SAMPLES_DIR

EXPECTED = {
    "tomato_early_blight.jpg": ("Tomato", "Early blight"),
    "tomato_late_blight.jpg": ("Tomato", "Late blight"),
    "potato_early_blight.jpg": ("Potato", "Early blight"),
    "corn_common_rust.jpg": ("Corn", "Common rust"),
    "grape_black_rot.jpg": ("Grape", "Black rot"),
}


def test_classify_leaf_on_samples():
    correct = 0
    for filename, (expected_crop, _expected_disease) in EXPECTED.items():
        path: Path = SAMPLES / filename
        if not path.exists():
            continue
        result = classify_leaf(path.read_bytes(), filename=filename)
        if result.crop == expected_crop or result.kb_key:
            correct += 1
    assert correct >= 4, f"expected >=4/5 samples classified plausibly, got {correct}"


def test_classify_leaf_never_raises_on_garbage():
    result = classify_leaf(b"not an image", filename="garbage.jpg")
    assert result.disease in ("Uncertain",) or result.crop == "Unknown"
