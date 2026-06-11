import json
import pytest
from unittest.mock import patch, MagicMock


def test_load_config_creates_defaults_when_no_file(tmp_path):
    config_file = str(tmp_path / "config.json")
    with patch("settings.CONFIG_PATH", config_file):
        from settings import load_config
        config = load_config()
    assert config["whisper_language"] == "de"
    assert config["whisper_model"] == "small"
    assert config["autostart"] is False
    assert config["hotkeys"]["transcribe"] == "ctrl+shift+y"
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
    assert config["hotkeys"]["transcribe"] == "ctrl+shift+y"


def test_set_autostart_enabled_writes_registry_value():
    fake_key = MagicMock()
    with patch("settings.winreg.OpenKey", return_value=fake_key), \
         patch("settings.winreg.SetValueEx") as set_value, \
         patch("settings.winreg.DeleteValue") as delete_value, \
         patch("settings.winreg.CloseKey"):
        from settings import set_autostart
        set_autostart(True)
    assert set_value.called
    assert set_value.call_args.args[1] == "Blitztext"
    assert not delete_value.called


def test_set_autostart_disabled_deletes_registry_value():
    fake_key = MagicMock()
    with patch("settings.winreg.OpenKey", return_value=fake_key), \
         patch("settings.winreg.SetValueEx") as set_value, \
         patch("settings.winreg.DeleteValue") as delete_value, \
         patch("settings.winreg.CloseKey"):
        from settings import set_autostart
        set_autostart(False)
    assert delete_value.called
    assert delete_value.call_args.args[1] == "Blitztext"
    assert not set_value.called


def test_set_autostart_disabled_ignores_missing_value():
    fake_key = MagicMock()
    with patch("settings.winreg.OpenKey", return_value=fake_key), \
         patch("settings.winreg.DeleteValue", side_effect=FileNotFoundError), \
         patch("settings.winreg.CloseKey"):
        from settings import set_autostart
        set_autostart(False)  # must not raise


def test_set_autostart_handles_registry_error():
    with patch("settings.winreg.OpenKey", side_effect=OSError):
        from settings import set_autostart
        set_autostart(True)  # must not raise
