import os
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def audio_file(tmp_path):
    p = tmp_path / "test.wav"
    p.write_bytes(b"RIFF fake wav data")
    return str(p)


def _mock_whisper(text: str):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": text}
    return mock_model


def test_transcribe_returns_text(audio_file):
    mock_model = _mock_whisper("Hallo Welt")
    with patch("transcriber.whisper.load_model", return_value=mock_model), \
         patch.dict("transcriber._model_cache", {}, clear=True):
        from transcriber import transcribe
        result = transcribe(audio_file, {"whisper_model": "base", "whisper_language": "de"})
    assert result == "Hallo Welt"


def test_transcribe_deletes_audio_file(audio_file):
    mock_model = _mock_whisper("Text")
    with patch("transcriber.whisper.load_model", return_value=mock_model), \
         patch.dict("transcriber._model_cache", {}, clear=True):
        from transcriber import transcribe
        transcribe(audio_file, {"whisper_model": "base", "whisper_language": "de"})
    assert not os.path.exists(audio_file)


def test_transcribe_passes_language(audio_file):
    mock_model = _mock_whisper("Test")
    with patch("transcriber.whisper.load_model", return_value=mock_model), \
         patch.dict("transcriber._model_cache", {}, clear=True):
        from transcriber import transcribe
        transcribe(audio_file, {"whisper_model": "base", "whisper_language": "de"})
    mock_model.transcribe.assert_called_once_with(audio_file, language="de")


def test_transcribe_caches_model(audio_file, tmp_path):
    mock_model = _mock_whisper("Text")
    audio_file2 = str(tmp_path / "test2.wav")
    with open(audio_file2, "wb") as f:
        f.write(b"RIFF data")
    with patch("transcriber.whisper.load_model", return_value=mock_model) as mock_load, \
         patch.dict("transcriber._model_cache", {}, clear=True):
        from transcriber import transcribe
        transcribe(audio_file, {"whisper_model": "base", "whisper_language": "de"})
        transcribe(audio_file2, {"whisper_model": "base", "whisper_language": "de"})
    assert mock_load.call_count == 1  # loaded once, reused second time


def test_transcribe_handles_remove_error(audio_file):
    mock_model = _mock_whisper("Text")
    with patch("transcriber.whisper.load_model", return_value=mock_model), \
         patch.dict("transcriber._model_cache", {}, clear=True), \
         patch("transcriber.os.remove", side_effect=FileNotFoundError):
        from transcriber import transcribe
        result = transcribe(audio_file, {"whisper_model": "base", "whisper_language": "de"})
    assert result == "Text"
