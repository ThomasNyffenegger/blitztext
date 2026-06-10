import threading
import time
import tkinter as tk

import keyboard

from overlay import Overlay
from recorder import AudioRecorder
from settings import load_config, set_autostart, SettingsWindow
from tray import TrayApp
import transcriber
import processor
import injector


class BlitzText:
    def __init__(self):
        self._config = load_config()
        set_autostart(self._config.get("autostart", False))
        self._recorder = AudioRecorder()
        self._active_mode: str | None = None
        self._mode_lock = threading.Lock()

        self._root = tk.Tk()
        self._root.withdraw()

        self._overlay = Overlay(self._root)
        self._settings_window = SettingsWindow(
            self._root, self._config, on_save=self._on_config_saved
        )
        self._tray = TrayApp(
            self._root,
            on_settings=self._settings_window.open,
            on_quit=self._quit,
        )

    def _on_config_saved(self, new_config: dict) -> None:
        self._config = new_config

    def _quit(self) -> None:
        self._root.destroy()

    def _start_mode(self, mode: str) -> None:
        with self._mode_lock:
            if self._active_mode:
                return
            self._active_mode = mode
        labels = {"transcribe": "🎙️ Transkription", "mail": "🎙️ Mail-Modus", "rage": "🎙️ Rage-Modus"}
        try:
            self._recorder.start()
        except Exception:
            with self._mode_lock:
                self._active_mode = None
            self._overlay.show("❌ Kein Mikrofon gefunden")
            return
        self._overlay.show(f"{labels[mode]} – Halten & sprechen...", persistent=True)

    def _stop_mode(self, mode: str) -> None:
        with self._mode_lock:
            if self._active_mode != mode:
                return
            self._active_mode = None
        model_name = self._config.get("whisper_model", "base")
        if transcriber.is_model_loaded(model_name):
            self._overlay.update_message("⏳ Wird transkribiert...")
        else:
            self._overlay.update_message("⏳ Modell wird geladen (einmalig)...")
        threading.Thread(target=self._process, args=(mode,), daemon=True).start()

    def _process(self, mode: str) -> None:
        audio_path = self._recorder.stop()
        if not audio_path:
            self._overlay.show("❌ Keine Aufnahme")
            return

        try:
            text = transcriber.transcribe(audio_path, self._config)
        except Exception as e:
            self._overlay.show(f"❌ Fehler: {type(e).__name__}")
            return
        if not text.strip():
            self._overlay.show("❌ Nichts erkannt – länger sprechen")
            return

        if mode in ("mail", "rage"):
            anthropic_key = self._config.get("anthropic_api_key", "")
            if not anthropic_key:
                self._overlay.hide()
                self._root.after(0, self._settings_window.open)
                return
            self._overlay.update_message("⏳ Claude formuliert um...")
            try:
                if mode == "mail":
                    text = processor.process_mail(text, self._config)
                else:
                    text = processor.process_rage(text, self._config)
            except Exception:
                self._overlay.show("❌ Fehler: Claude API nicht erreichbar")
                return

        injector.inject_text(text)
        self._overlay.show("✓ Fertig", duration=2.0)

    def _hotkey_listener(self) -> None:
        state: dict[str, bool] = {}
        while True:
            hotkeys = self._config["hotkeys"]
            for mode in list(state):
                if mode not in hotkeys:
                    del state[mode]
            for mode in hotkeys:
                if mode not in state:
                    state[mode] = False
            for mode, hotkey in hotkeys.items():
                pressed = keyboard.is_pressed(hotkey)
                if pressed and not state[mode]:
                    state[mode] = True
                    threading.Thread(target=self._start_mode, args=(mode,), daemon=True).start()
                elif not pressed and state[mode]:
                    state[mode] = False
                    threading.Thread(target=self._stop_mode, args=(mode,), daemon=True).start()
            time.sleep(0.05)

    def _preload_model(self) -> None:
        model_name = self._config.get("whisper_model", "base")
        transcriber.preload_model(model_name)

    def run(self) -> None:
        self._tray.run()
        threading.Thread(target=self._preload_model, daemon=True).start()
        hotkey_thread = threading.Thread(target=self._hotkey_listener, daemon=True)
        hotkey_thread.start()
        self._root.mainloop()


if __name__ == "__main__":
    import sys
    import traceback
    try:
        app = BlitzText()
        app.run()
    except Exception:
        traceback.print_exc()
        input("Fehler — Enter zum Beenden")
