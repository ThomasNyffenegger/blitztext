from unittest.mock import patch

import modes


def test_whisper_task_translate():
    assert modes.whisper_task_for("translate") == "translate"


def test_whisper_task_transcribe_for_other_modes():
    assert modes.whisper_task_for("transcribe") == "transcribe"
    assert modes.whisper_task_for("mail") == "transcribe"
    assert modes.whisper_task_for("rage") == "transcribe"


def test_needs_claude():
    assert modes.needs_claude("mail") is True
    assert modes.needs_claude("rage") is True
    assert modes.needs_claude("transcribe") is False
    assert modes.needs_claude("translate") is False


def test_mode_label_known():
    assert modes.mode_label("translate") == "🎙️ Übersetzung → EN"
    assert modes.mode_label("transcribe") == "🎙️ Transkription"


def test_mode_label_unknown_falls_back_to_name():
    assert modes.mode_label("unknown") == "unknown"


def test_apply_claude_mail_calls_processor():
    with patch("modes.processor.process_mail", return_value="formatierte Mail") as m:
        result = modes.apply_claude("mail", "roher Text", {"k": "v"})
    m.assert_called_once_with("roher Text", {"k": "v"})
    assert result == "formatierte Mail"


def test_apply_claude_rage_calls_processor():
    with patch("modes.processor.process_rage", return_value="wütender Text") as m:
        result = modes.apply_claude("rage", "roher Text", {"k": "v"})
    m.assert_called_once_with("roher Text", {"k": "v"})
    assert result == "wütender Text"


def test_apply_claude_unknown_mode_returns_text_unchanged():
    assert modes.apply_claude("transcribe", "unverändert", {}) == "unverändert"
