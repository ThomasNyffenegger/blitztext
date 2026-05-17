import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "openai_api_key": "",
    "anthropic_api_key": "",
    "whisper_model": "whisper-1",
    "whisper_language": "de",
    "autostart": False,
    "hotkeys": {
        "transcribe": "ctrl+alt+space",
        "mail": "ctrl+alt+m",
        "rage": "ctrl+alt+r",
    },
}


def load_config() -> dict:
    config = DEFAULT_CONFIG.copy()
    config["hotkeys"] = DEFAULT_CONFIG["hotkeys"].copy()
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        config.update({k: v for k, v in saved.items() if k != "hotkeys"})
        if "hotkeys" in saved:
            config["hotkeys"].update(saved["hotkeys"])
    return config


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
