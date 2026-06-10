import json
import pytest
from unittest.mock import patch


def test_load_config_creates_defaults_when_no_file(tmp_path):
    config_file = str(tmp_path / "config.json")
    with patch("settings.CONFIG_PATH", config_file):
        from settings import load_config
        config = load_config()
    assert config["whisper_language"] == "de"
    assert config["whisper_model"] == "small"
    assert config["autostart"] is False
    assert config["hotkeys"]["transcribe"] == "ctrl+alt+space"
    assert config["hotkeys"]["mail"] == "ctrl+alt+m"
    assert config["hotkeys"]["rage"] == "ctrl+alt+r"


def test_save_and_load_config_roundtrip(tmp_path):
    config_file = str(tmp_path / "config.json")
    with patch("settings.CONFIG_PATH", config_file):
        from settings import load_config, save_config
        config = load_config()
        config["openai_api_key"] = "sk-test-123"
        save_config(config)
        loaded = load_config()
    assert loaded["openai_api_key"] == "sk-test-123"


def test_load_config_merges_missing_keys(tmp_path):
    config_file = str(tmp_path / "config.json")
    # Write partial config
    with open(config_file, "w") as f:
        json.dump({"openai_api_key": "existing-key"}, f)
    with patch("settings.CONFIG_PATH", config_file):
        from settings import load_config
        config = load_config()
    assert config["openai_api_key"] == "existing-key"
    assert config["whisper_language"] == "de"  # default filled in


def test_load_config_returns_defaults_on_corrupted_file(tmp_path):
    config_file = str(tmp_path / "config.json")
    # Write corrupted JSON
    with open(config_file, "w") as f:
        f.write("{invalid json content")
    with patch("settings.CONFIG_PATH", config_file):
        from settings import load_config
        config = load_config()
    # Should return defaults gracefully
    assert config["whisper_language"] == "de"
    assert config["whisper_model"] == "small"
    assert config["autostart"] is False
    assert config["hotkeys"]["transcribe"] == "ctrl+alt+space"
