import json
import os
import sys
import threading
import winreg
import tkinter as tk
from tkinter import ttk

import transcriber


def _fmt_mb(num_bytes: int) -> str:
    return f"{num_bytes / (1024 * 1024):.0f} MB"

_AUTOSTART_KEY = "Blitztext"
_AUTOSTART_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

MODEL_OPTIONS = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
MODEL_MEMORY = {
    "tiny":    "~75 MB",
    "base":    "~145 MB",
    "small":   "~466 MB",
    "medium":  "~1.5 GB",
    "large":   "~3 GB",
    "large-v2":"~3 GB",
    "large-v3":"~3 GB",
}


def set_autostart(enabled: bool) -> None:
    exe = sys.executable
    script = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _AUTOSTART_PATH, access=winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, _AUTOSTART_KEY, 0, winreg.REG_SZ, f'"{exe}" "{script}"')
        else:
            try:
                winreg.DeleteValue(key, _AUTOSTART_KEY)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except OSError:
        pass


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "anthropic_api_key": "",
    "whisper_model": "small",
    "whisper_language": "de",
    "autostart": False,
    "hotkeys": {
        "transcribe": "ctrl+shift+y",
        "translate": "ctrl+shift+e",
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
            pass
    return config


def save_config(config: dict) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except OSError:
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
        self._cancel_event: threading.Event | None = None
        self._window = tk.Toplevel(self._root)
        self._window.title("Blitztext – Einstellungen")
        self._window.resizable(False, False)
        self._window.grab_set()
        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 4}
        frame = ttk.Frame(self._window, padding=16)
        frame.grid(sticky="nsew")

        # API Key
        ttk.Label(frame, text="Anthropic API Key:").grid(row=0, column=0, sticky="w", **pad)
        self._api_key_var = tk.StringVar(value=self._config.get("anthropic_api_key", ""))
        entry = ttk.Entry(frame, textvariable=self._api_key_var, width=42, show="•")
        entry.grid(row=0, column=1, **pad)

        # Whisper Sprache
        ttk.Label(frame, text="Whisper Sprache:").grid(row=1, column=0, sticky="w", **pad)
        self._language_var = tk.StringVar(value=self._config.get("whisper_language", "de"))
        ttk.Entry(frame, textvariable=self._language_var, width=42).grid(row=1, column=1, **pad)

        ttk.Separator(frame).grid(row=2, columnspan=2, sticky="ew", pady=8)

        # Whisper Modell – Dropdown
        ttk.Label(frame, text="Whisper Modell:").grid(row=3, column=0, sticky="w", **pad)
        self._model_var = tk.StringVar(value=self._config.get("whisper_model", "small"))
        combo = ttk.Combobox(frame, textvariable=self._model_var, values=MODEL_OPTIONS,
                             state="readonly", width=15)
        combo.grid(row=3, column=1, sticky="w", **pad)
        combo.bind("<<ComboboxSelected>>", self._on_model_changed)

        # Modell-Info: Speicher + Ladestatus
        self._model_info_var = tk.StringVar()
        ttk.Label(frame, textvariable=self._model_info_var, foreground="gray").grid(
            row=4, column=1, sticky="w", padx=10, pady=0)

        # Laden-/Stop-Button + Fortschrittsbalken
        model_btn_frame = ttk.Frame(frame)
        model_btn_frame.grid(row=5, column=1, sticky="w", padx=10, pady=4)

        self._load_btn = ttk.Button(model_btn_frame, text="Modell laden",
                                    command=self._load_model)
        self._load_btn.pack(side="left")

        self._stop_btn = ttk.Button(model_btn_frame, text="Stop",
                                    command=self._stop_load, state="disabled")
        self._stop_btn.pack(side="left", padx=(6, 0))

        self._progress = ttk.Progressbar(model_btn_frame, mode="determinate",
                                         length=120, maximum=100)
        self._progress.pack(side="left", padx=(8, 0))

        self._progress_var = tk.StringVar()
        ttk.Label(model_btn_frame, textvariable=self._progress_var,
                  foreground="gray", width=6).pack(side="left", padx=(6, 0))

        self._update_model_info()

        ttk.Separator(frame).grid(row=6, columnspan=2, sticky="ew", pady=8)

        # Hotkeys
        hotkeys = self._config.get("hotkeys", {})
        hotkey_fields = [
            ("Hotkey Transkription:", "transcribe"),
            ("Hotkey Übersetzung → EN:", "translate"),
            ("Hotkey Mail:", "mail"),
            ("Hotkey Rage:", "rage"),
        ]
        self._hotkey_vars: dict[str, tk.StringVar] = {}
        row = 7
        for label, key in hotkey_fields:
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", **pad)
            var = tk.StringVar(value=hotkeys.get(key, ""))
            self._hotkey_vars[key] = var
            ttk.Entry(frame, textvariable=var, width=42).grid(row=row, column=1, **pad)
            row += 1

        ttk.Separator(frame).grid(row=row, columnspan=2, sticky="ew", pady=8)
        row += 1

        self._autostart_var = tk.BooleanVar(value=self._config.get("autostart", False))
        ttk.Checkbutton(frame, text="Autostart mit Windows",
                        variable=self._autostart_var).grid(
            row=row, column=0, columnspan=2, sticky="w", **pad)
        row += 1

        ttk.Button(frame, text="Speichern", command=self._save).grid(
            row=row, column=1, sticky="e", **pad)
        ttk.Button(frame, text="Abbrechen", command=self._window.destroy).grid(
            row=row, column=0, sticky="w", **pad)

    def _on_model_changed(self, _event=None) -> None:
        self._update_model_info()

    def _update_model_info(self) -> None:
        model = self._model_var.get()
        memory = MODEL_MEMORY.get(model, "")
        if transcriber.is_model_loaded(model):
            status = "✓ im RAM geladen"
            btn_state = "disabled"
        elif transcriber.is_model_downloaded(model):
            status = "heruntergeladen (Klick zum Laden)"
            btn_state = "normal"
        else:
            status = "nicht heruntergeladen"
            btn_state = "normal"
        self._model_info_var.set(f"{memory}  –  {status}")
        self._load_btn.configure(state=btn_state)
        self._stop_btn.configure(state="disabled")
        self._progress.configure(value=0)
        self._progress_var.set("")

    def _load_model(self) -> None:
        model = self._model_var.get()
        self._cancel_event = threading.Event()
        self._load_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._progress.configure(value=0)

        def _worker():
            try:
                if not transcriber.is_model_downloaded(model):
                    self._root.after(0, lambda: self._model_info_var.set(
                        f"{MODEL_MEMORY.get(model, '')}  –  wird heruntergeladen…"))
                    transcriber.download_model(
                        model,
                        progress_cb=self._on_progress,
                        cancel_event=self._cancel_event,
                    )
                # Datei ist da → ins RAM laden (Stop hier nicht mehr möglich)
                self._root.after(0, self._enter_ram_load_state)
                transcriber.preload_model(model)
                self._root.after(0, self._on_load_done)
            except transcriber.DownloadCancelled:
                self._root.after(0, self._on_load_cancelled)
            except Exception as e:
                self._root.after(0, lambda: self._on_load_error(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_progress(self, downloaded: int, total: int) -> None:
        def _update():
            if total > 0:
                pct = downloaded * 100 / total
                self._progress.configure(value=pct)
                self._progress_var.set(f"{pct:.0f}%")
                self._model_info_var.set(
                    f"{_fmt_mb(downloaded)} / {_fmt_mb(total)}  –  wird heruntergeladen…")
        self._root.after(0, _update)

    def _enter_ram_load_state(self) -> None:
        self._stop_btn.configure(state="disabled")
        self._progress.configure(value=100)
        self._progress_var.set("RAM…")
        self._model_info_var.set(
            f"{MODEL_MEMORY.get(self._model_var.get(), '')}  –  wird ins RAM geladen…")

    def _stop_load(self) -> None:
        if self._cancel_event is not None:
            self._cancel_event.set()
        self._stop_btn.configure(state="disabled")

    def _on_load_done(self) -> None:
        self._update_model_info()

    def _on_load_cancelled(self) -> None:
        self._update_model_info()
        self._model_info_var.set(
            f"{MODEL_MEMORY.get(self._model_var.get(), '')}  –  Abgebrochen")

    def _on_load_error(self, error: Exception) -> None:
        self._update_model_info()
        self._model_info_var.set(f"❌ Fehler: {type(error).__name__}")

    def _save(self) -> None:
        self._config["anthropic_api_key"] = self._api_key_var.get()
        self._config["whisper_language"] = self._language_var.get()
        self._config["whisper_model"] = self._model_var.get()
        for key, var in self._hotkey_vars.items():
            self._config["hotkeys"][key] = var.get()
        self._config["autostart"] = self._autostart_var.get()
        save_config(self._config)
        set_autostart(self._config["autostart"])
        self._on_save(self._config)
        self._window.destroy()
