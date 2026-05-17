import os
import numpy as np
import pytest
from unittest.mock import MagicMock, patch, call


def test_recorder_is_not_recording_initially():
    from recorder import AudioRecorder
    rec = AudioRecorder()
    assert rec.is_recording is False


def test_recorder_start_opens_stream():
    from recorder import AudioRecorder
    with patch("recorder.sd.InputStream") as MockStream:
        mock_stream = MagicMock()
        MockStream.return_value = mock_stream
        rec = AudioRecorder()
        rec.start()
        mock_stream.start.assert_called_once()
        assert rec.is_recording is True


def test_recorder_stop_returns_wav_path(tmp_path):
    from recorder import AudioRecorder
    with patch("recorder.sd.InputStream") as MockStream, \
         patch("recorder.os.path.dirname", return_value=str(tmp_path)):
        mock_stream = MagicMock()
        MockStream.return_value = mock_stream
        rec = AudioRecorder()
        rec.start()
        fake_audio = np.zeros((1600, 1), dtype="int16")
        rec._callback(fake_audio, 1600, None, None)
        path = rec.stop()
    assert path is not None
    assert path.endswith(".wav")
    assert os.path.exists(path)
    assert rec.is_recording is False


def test_recorder_stop_without_audio_returns_none():
    from recorder import AudioRecorder
    with patch("recorder.sd.InputStream") as MockStream:
        mock_stream = MagicMock()
        MockStream.return_value = mock_stream
        rec = AudioRecorder()
        rec.start()
        path = rec.stop()
    assert path is None
