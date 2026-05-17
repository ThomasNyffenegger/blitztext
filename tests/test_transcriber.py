import os
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def audio_file(tmp_path):
    p = tmp_path / "test.wav"
    p.write_bytes(b"RIFF fake wav data")
    return str(p)


def test_transcribe_returns_text(audio_file):
    mock_response = MagicMock()
    mock_response.text = "Hallo Welt"
    with patch("transcriber.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_client.audio.transcriptions.create.return_value = mock_response
        from transcriber import transcribe
        result = transcribe(audio_file, {
            "openai_api_key": "sk-test",
            "whisper_model": "whisper-1",
            "whisper_language": "de",
        })
    assert result == "Hallo Welt"


def test_transcribe_deletes_audio_file(audio_file):
    mock_response = MagicMock()
    mock_response.text = "Text"
    with patch("transcriber.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_client.audio.transcriptions.create.return_value = mock_response
        from transcriber import transcribe
        transcribe(audio_file, {
            "openai_api_key": "sk-test",
            "whisper_model": "whisper-1",
            "whisper_language": "de",
        })
    assert not os.path.exists(audio_file)


def test_transcribe_passes_language_and_model(audio_file):
    mock_response = MagicMock()
    mock_response.text = "Test"
    with patch("transcriber.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_client.audio.transcriptions.create.return_value = mock_response
        from transcriber import transcribe
        transcribe(audio_file, {
            "openai_api_key": "sk-key",
            "whisper_model": "whisper-1",
            "whisper_language": "de",
        })
    kwargs = mock_client.audio.transcriptions.create.call_args.kwargs
    assert kwargs["model"] == "whisper-1"
    assert kwargs["language"] == "de"
