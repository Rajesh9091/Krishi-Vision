import numpy as np
import soundfile as sf

from app.services import asr


def test_transcribe_silence_returns_could_not_hear(tmp_path):
    wav_path = tmp_path / "silence.wav"
    sf.write(str(wav_path), np.zeros(16000, dtype=np.float32), 16000)

    result = asr.transcribe(str(wav_path), "en")

    assert result["text"] == ""
    assert result["error"] == "could_not_hear"


def test_transcribe_missing_file_falls_back_gracefully():
    result = asr.transcribe("does_not_exist.wav", "en")

    assert result["text"] == ""
    assert result["error"] == "could_not_hear"
