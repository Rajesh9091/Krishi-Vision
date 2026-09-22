import soundfile as sf

from app.services import tts
from app.settings import settings


def test_clean_for_tts_strips_markdown_and_units():
    cleaned = tts.clean_for_tts("**Spray** 5 ml/L, 50% coverage. See https://example.com #tip")
    assert "*" not in cleaned
    assert "https://" not in cleaned
    assert "percent" in cleaned


def test_synthesize_produces_wav_over_1s():
    result = tts.synthesize("This is a short crop care message for testing purposes today.", "en")
    assert result["audio_url"] is not None
    audio_path = settings.AUDIO_DIR / result["audio_url"].split("/")[-1]
    assert audio_path.exists()
    data, sample_rate = sf.read(str(audio_path))
    assert sample_rate == 16000
    assert len(data) / sample_rate > 1.0
