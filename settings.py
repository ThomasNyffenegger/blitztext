import json
import os
import tkinter as tk
from tkinter import ttk

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "openai_api_key": "",
    "anthropic_api_key": "",
    "whisper_model": "base",
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
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config.update({k: v for k, v in saved.items() if k != "hotkeys"})
            if "hotkeys" in saved:
                config["hotkeys"].update(saved["hotkeys"])
        except (json.JSONDecodeError, OSError):
            # Corrupted or unreadable config file; return defaults
            pass
    return config


def save_config(config: dict) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except OSError:
        # Unable to write config file; silently ignore
        pass


class SettingsWindow:
    def __init__(self, root: tk.Tk, config: dict, on_save: callable):
        self._root = root
        self._config = config
        self._on_save = on_save
        self._window: tk.Toplevel | None = None

    def open(self) -> None:
        if self._window and self._window.winfo_exists():
            self._window.lift()
            return
        self._window = tk.Toplevel(self._root)
        self._window.title("Blitztext – Einstellungen")
        self._window.resizable(False, False)
        self._window.grab_set()
        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 4}
        frame = ttk.Frame(self._window, padding=16)
        frame.grid(sticky="nsew")

        fields = [
            ("OpenAI API Key:", "openai_api_key"),
            ("Anthropic API Key:", "anthropic_api_key"),
            ("Whisper Modell:", "whisper_model"),
            ("Whisper Sprache:", "whisper_language"),
        ]
        self._vars: dict[str, tk.StringVar] = {}
        for row, (label, key) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", **pad)
            var = tk.StringVar(value=self._config.get(key, ""))
            self._vars[key] = var
            entry = ttk.Entry(frame, textvariable=var, width=42)
            if "key" in key.lower():
                entry.configure(show="•")
            entry.grid(row=row, column=1, **pad)

        ttk.Separator(frame).grid(row=len(fields), columnspan=2, sticky="ew", pady=8)

        hotkeys = self._config.get("hotkeys", {})
        hotkey_fields = [
            ("Hotkey Transkription:", "transcribe"),
            ("Hotkey Mail:", "mail"),
            ("Hotkey Rage:", "rage"),
        ]
        self._hotkey_vars: dict[str, tk.StringVar] = {}
        for i, (label, key) in enumerate(hotkey_fields):
            row = len(fields) + 1 + i
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", **pad)
            var = tk.StringVar(value=hotkeys.get(key, ""))
            self._hotkey_vars[key] = var
            ttk.Entry(frame, textvariable=var, width=42).grid(row=row, column=1, **pad)

        auto_row = len(fields) + 1 + len(hotkey_fields)
        ttk.Separator(frame).grid(row=auto_row, columnspan=2, sticky="ew", pady=8)

        self._autostart_var = tk.BooleanVar(value=self._config.get("autostart", False))
        ttk.Checkbutton(frame, text="Autostart mit Windows", variable=self._autostart_var).grid(
            row=auto_row + 1, column=0, columnspan=2, sticky="w", **pad
        )

        btn_row = auto_row + 2
        ttk.Button(frame, text="Speichern", command=self._save).grid(
            row=btn_row, column=1, sticky="e", **pad
        )
        ttk.Button(frame, text="Abbrechen", command=self._window.destroy).grid(
            row=btn_row, column=0, sticky="w", **pad
        )

    def _save(self) -> None:
        for key, var in self._vars.items():
            self._config[key] = var.get()
        for key, var in self._hotkey_vars.items():
            self._config["hotkeys"][key] = var.get()
        self._config["autostart"] = self._autostart_var.get()
        save_config(self._config)
        self._on_save(self._config)
        self._window.destroy()
