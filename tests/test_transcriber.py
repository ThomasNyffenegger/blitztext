import os
import numpy as np
import scipy.io.wavfile as wav
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def audio_file(tmp_path):
    p = tmp_path / "test.wav"
    audio = np.zeros(16000, dtype="int16")  # 1 second of silence
    wav.write(str(p), 16000, audio)
    return str(p)


def _segment(text: str):
    seg = MagicMock()
    seg.text = text
    return seg


def _mock_whisper(text: str):
    """A faster-whisper model whose transcribe() yields one segment plus info."""
    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([_segment(text)], MagicMock())
    return mock_model


def test_transcribe_returns_text(audio_file):
    mock_model = _mock_whisper("Hallo Welt")
    with patch("transcriber.WhisperModel", return_value=mock_model), \
         patch.dict("transcriber._model_cache", {}, clear=True):
        from transcriber import transcribe
        result = transcribe(audio_file, {"whisper_model": "small", "whisper_language": "de"})
    assert result == "Hallo Welt"


def test_transcribe_joins_multiple_segments(audio_file):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = (
        [_segment("Hallo "), _segment("schöne "), _segment("Welt")],
        MagicMock(),
    )
    with patch("transcriber.WhisperModel", return_value=mock_model), \
         patch.dict("transcriber._model_cache", {}, clear=True):
        from transcriber import transcribe
        result = transcribe(audio_file, {"whisper_model": "small", "whisper_language": "de"})
    assert result == "Hallo schöne Welt"


def test_transcribe_deletes_audio_file(audio_file):
    mock_model = _mock_whisper("Text")
    with patch("transcriber.WhisperModel", return_value=mock_model), \
         patch.dict("transcriber._model_cache", {}, clear=True):
        from transcriber import transcribe
        transcribe(audio_file, {"whisper_model": "small", "whisper_language": "de"})
    assert not os.path.exists(audio_file)


def test_transcribe_passes_language(audio_file):
    mock_model = _mock_whisper("Test")
    with patch("transcriber.WhisperModel", return_value=mock_model), \
         patch.dict("transcriber._model_cache", {}, clear=True):
        from transcriber import transcribe
        transcribe(audio_file, {"whisper_model": "small", "whisper_language": "de"})
    assert mock_model.transcribe.call_args.kwargs.get("language") == "de"


def test_transcribe_defaults_to_transcribe_task(audio_file):
    mock_model = _mock_whisper("Test")
    with patch("transcriber.WhisperModel", return_value=mock_model), \
         patch.dict("transcriber._model_cache", {}, clear=True):
        from transcriber import transcribe
        transcribe(audio_file, {"whisper_model": "small", "whisper_language": "de"})
    assert mock_model.transcribe.call_args.kwargs.get("task") == "transcribe"


def test_transcribe_passes_translate_task(audio_file):
    mock_model = _mock_whisper("Hello World")
    with patch("transcriber.WhisperModel", return_value=mock_model), \
         patch.dict("transcriber._model_cache", {}, clear=True):
        from transcriber import transcribe
        result = transcribe(
            audio_file, {"whisper_model": "small", "whisper_language": "de"}, task="translate"
        )
    assert mock_model.transcribe.call_args.kwargs.get("task") == "translate"
    assert result == "Hello World"


def test_transcribe_caches_model(tmp_path):
    mock_model = _mock_whisper("Text")
    for i in range(2):
        p = tmp_path / f"test{i}.wav"
        wav.write(str(p), 16000, np.zeros(16000, dtype="int16"))
    files = [str(tmp_path / f"test{i}.wav") for i in range(2)]
    with patch("transcriber.WhisperModel", return_value=mock_model) as mock_load, \
         patch.dict("transcriber._model_cache", {}, clear=True):
        from transcriber import transcribe
        transcribe(files[0], {"whisper_model": "small", "whisper_language": "de"})
        transcribe(files[1], {"whisper_model": "small", "whisper_language": "de"})
    assert mock_load.call_count == 1


def test_transcribe_handles_remove_error(audio_file):
    mock_model = _mock_whisper("Text")
    with patch("transcriber.WhisperModel", return_value=mock_model), \
         patch.dict("transcriber._model_cache", {}, clear=True), \
         patch("transcriber.os.remove", side_effect=FileNotFoundError):
        from transcriber import transcribe
        result = transcribe(audio_file, {"whisper_model": "small", "whisper_language": "de"})
    assert result == "Text"
