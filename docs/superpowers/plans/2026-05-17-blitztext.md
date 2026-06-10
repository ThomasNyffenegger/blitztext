# Blitztext Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows system-tray Python app that records speech via hotkey, transcribes via OpenAI Whisper, optionally reformats via Claude, and pastes the text at the cursor.

**Architecture:** A hidden tkinter root window serves as the GUI thread; pystray runs in a background thread; a polling hotkey thread detects hold-to-record keypresses; all recording/API/injection work runs in daemon threads. The overlay and settings window are tkinter Toplevel windows scheduled via `root.after()` for thread safety.

**Tech Stack:** Python 3.11+, `keyboard`, `sounddevice`, `scipy`, `openai`, `anthropic`, `pyperclip`, `pyautogui`, `pystray`, `Pillow`, `tkinter` (stdlib)

---

## File Map

| File | Responsibility |
|------|---------------|
| `settings.py` | `load_config` / `save_config` + `SettingsWindow` tkinter UI |
| `recorder.py` | `AudioRecorder` — sounddevice stream → temp WAV |
| `transcriber.py` | `transcribe(audio_path, config)` → Whisper API → str |
| `injector.py` | `inject_text(text)` — clipboard save/paste/restore |
| `overlay.py` | `Overlay` — tkinter Toplevel, thread-safe via `root.after()` |
| `processor.py` | `process_mail` / `process_rage` — Claude API |
| `tray.py` | `TrayApp` — pystray icon + menu, runs in thread |
| `main.py` | Wire all modules; hotkey polling loop; `tkinter.mainloop()` |

---

### Task 1: Git init + project structure

**Files:**
- Create: `.gitignore`
- Create: `tests/__init__.py`

- [ ] **Step 1: Init git repo and create .gitignore**

```bash
cd D:\Claude\Projekte\BlitzText
git init
```

Create `.gitignore`:
```
config.json
temp_audio.wav
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
build/
.venv/
venv/
```

- [ ] **Step 2: Create tests directory**

```bash
mkdir tests
echo. > tests/__init__.py
```

- [ ] **Step 3: Install dependencies**

```bash
pip install openai>=1.30.0 anthropic>=0.25.0 sounddevice>=0.4.6 scipy>=1.11.0 keyboard>=0.13.5 pyperclip>=1.8.2 pyautogui>=0.9.54 pystray>=0.19.5 Pillow>=10.0.0 pytest>=8.0.0
```

- [ ] **Step 4: First commit**

```bash
git add .gitignore requirements.txt tests/__init__.py
git commit -m "chore: project setup with dependencies"
```

---

### Task 2: settings.py — config I/O

**Files:**
- Create: `settings.py`
- Create: `tests/test_settings.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_settings.py`:
```python
import json
import pytest
from unittest.mock import patch


def test_load_config_creates_defaults_when_no_file(tmp_path):
    config_file = str(tmp_path / "config.json")
    with patch("settings.CONFIG_PATH", config_file):
        from settings import load_config
        config = load_config()
    assert config["whisper_language"] == "de"
    assert config["whisper_model"] == "whisper-1"
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd D:\Claude\Projekte\BlitzText
pytest tests/test_settings.py -v
```
Expected: `ModuleNotFoundError: No module named 'settings'`

- [ ] **Step 3: Implement config I/O in settings.py**

Create `settings.py`:
```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_settings.py -v
```
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add settings.py tests/test_settings.py
git commit -m "feat: config load/save with defaults and merge"
```

---

### Task 3: recorder.py — audio capture

**Files:**
- Create: `recorder.py`
- Create: `tests/test_recorder.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_recorder.py`:
```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_recorder.py -v
```
Expected: `ModuleNotFoundError: No module named 'recorder'`

- [ ] **Step 3: Implement recorder.py**

Create `recorder.py`:
```python
import os
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav


class AudioRecorder:
    SAMPLE_RATE = 16000
    CHANNELS = 1

    def __init__(self):
        self._recording = False
        self._frames = []
        self._stream = None

    def start(self) -> None:
        self._frames = []
        self._recording = True
        self._stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype="int16",
            callback=self._callback,
        )
        self._stream.start()

    def _callback(self, indata, frames, time, status):
        if self._recording:
            self._frames.append(indata.copy())

    def stop(self) -> str | None:
        self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if not self._frames:
            return None
        audio = np.concatenate(self._frames, axis=0)
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_audio.wav")
        wav.write(path, self.SAMPLE_RATE, audio)
        return path

    @property
    def is_recording(self) -> bool:
        return self._recording
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_recorder.py -v
```
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add recorder.py tests/test_recorder.py
git commit -m "feat: AudioRecorder with sounddevice stream and WAV export"
```

---

### Task 4: transcriber.py — Whisper API

**Files:**
- Create: `transcriber.py`
- Create: `tests/test_transcriber.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_transcriber.py`:
```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_transcriber.py -v
```
Expected: `ModuleNotFoundError: No module named 'transcriber'`

- [ ] **Step 3: Implement transcriber.py**

Create `transcriber.py`:
```python
import os
from openai import OpenAI


def transcribe(audio_path: str, config: dict) -> str:
    client = OpenAI(api_key=config["openai_api_key"])
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model=config.get("whisper_model", "whisper-1"),
            file=f,
            language=config.get("whisper_language", "de"),
        )
    os.remove(audio_path)
    return result.text
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_transcriber.py -v
```
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add transcriber.py tests/test_transcriber.py
git commit -m "feat: Whisper transcription with file cleanup"
```

---

### Task 5: injector.py — clipboard-based text insertion

**Files:**
- Create: `injector.py`
- Create: `tests/test_injector.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_injector.py`:
```python
from unittest.mock import patch, call


def test_inject_text_pastes_text():
    with patch("injector.pyperclip.paste", return_value="original"), \
         patch("injector.pyperclip.copy") as mock_copy, \
         patch("injector.pyautogui.hotkey") as mock_hotkey, \
         patch("injector.time.sleep"):
        from injector import inject_text
        inject_text("injizierter Text")
    mock_hotkey.assert_called_once_with("ctrl", "v")
    assert mock_copy.call_args_list[0] == call("injizierter Text")


def test_inject_text_restores_clipboard():
    with patch("injector.pyperclip.paste", return_value="Originalinhalt"), \
         patch("injector.pyperclip.copy") as mock_copy, \
         patch("injector.pyautogui.hotkey"), \
         patch("injector.time.sleep"):
        from injector import inject_text
        inject_text("neuer Text")
    assert mock_copy.call_args_list[-1] == call("Originalinhalt")


def test_inject_text_handles_empty_clipboard():
    with patch("injector.pyperclip.paste", side_effect=Exception("no clipboard")), \
         patch("injector.pyperclip.copy") as mock_copy, \
         patch("injector.pyautogui.hotkey"), \
         patch("injector.time.sleep"):
        from injector import inject_text
        inject_text("Text")
    assert mock_copy.call_args_list[0] == call("Text")
    assert mock_copy.call_args_list[-1] == call("")
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_injector.py -v
```
Expected: `ModuleNotFoundError: No module named 'injector'`

- [ ] **Step 3: Implement injector.py**

Create `injector.py`:
```python
import time
import pyperclip
import pyautogui


def inject_text(text: str) -> None:
    try:
        original = pyperclip.paste()
    except Exception:
        original = ""

    pyperclip.copy(text)
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.1)
    pyperclip.copy(original)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_injector.py -v
```
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add injector.py tests/test_injector.py
git commit -m "feat: clipboard-based text injection with restore"
```

---

### Task 6: overlay.py — tkinter feedback overlay

**Files:**
- Create: `overlay.py`

No unit tests — tkinter windows cannot be instantiated in headless test environments. Manual verification in Task 10.

- [ ] **Step 1: Implement overlay.py**

Create `overlay.py`:
```python
import tkinter as tk


class Overlay:
    """Thread-safe overlay window. All tkinter calls dispatched via root.after()."""

    def __init__(self, root: tk.Tk):
        self._root = root
        self._window: tk.Toplevel | None = None

    def show(self, message: str, duration: float = 2.0, persistent: bool = False) -> None:
        self._root.after(0, lambda: self._show(message, duration, persistent))

    def update_message(self, message: str) -> None:
        self._root.after(0, lambda: self._update(message))

    def hide(self) -> None:
        self._root.after(0, self._hide)

    def _show(self, message: str, duration: float, persistent: bool) -> None:
        self._hide()
        self._window = tk.Toplevel(self._root)
        self._window.overrideredirect(True)
        self._window.attributes("-topmost", True)
        self._window.attributes("-alpha", 0.88)
        self._window.configure(bg="#1e1e1e")
        self._window.resizable(False, False)

        label = tk.Label(
            self._window,
            text=message,
            font=("Segoe UI", 11),
            fg="white",
            bg="#1e1e1e",
            padx=18,
            pady=10,
        )
        label.pack()
        self._window.update_idletasks()

        screen_w = self._root.winfo_screenwidth()
        w = self._window.winfo_width()
        self._window.geometry(f"+{screen_w - w - 20}+20")

        if not persistent:
            self._window.after(int(duration * 1000), self._hide)

    def _update(self, message: str) -> None:
        if self._window:
            for widget in self._window.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.configure(text=message)

    def _hide(self) -> None:
        if self._window:
            self._window.destroy()
            self._window = None
```

- [ ] **Step 2: Commit**

```bash
git add overlay.py
git commit -m "feat: thread-safe tkinter overlay (top-right, semi-transparent)"
```

---

### Task 7: processor.py — Claude API text reformatting

**Files:**
- Create: `processor.py`
- Create: `tests/test_processor.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_processor.py`:
```python
from unittest.mock import MagicMock, patch
import processor as proc


CONFIG = {"anthropic_api_key": "test-key"}


def _mock_anthropic(response_text: str):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=response_text)]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    return mock_client


def test_process_mail_uses_mail_prompt():
    mock_client = _mock_anthropic("Sehr geehrte Damen und Herren...")
    with patch("processor.Anthropic", return_value=mock_client):
        result = proc.process_mail("hey schick mal die datei", CONFIG)
    assert result == "Sehr geehrte Damen und Herren..."
    kwargs = mock_client.messages.create.call_args.kwargs
    assert kwargs["system"] == proc.MAIL_PROMPT
    assert kwargs["messages"][0]["content"] == "hey schick mal die datei"


def test_process_rage_uses_rage_prompt():
    mock_client = _mock_anthropic("ICH BIN SO WÜTEND!!!")
    with patch("processor.Anthropic", return_value=mock_client):
        result = proc.process_rage("das meeting war langweilig", CONFIG)
    assert result == "ICH BIN SO WÜTEND!!!"
    kwargs = mock_client.messages.create.call_args.kwargs
    assert kwargs["system"] == proc.RAGE_PROMPT


def test_process_mail_uses_correct_model():
    mock_client = _mock_anthropic("E-Mail Text")
    with patch("processor.Anthropic", return_value=mock_client):
        proc.process_mail("text", CONFIG)
    kwargs = mock_client.messages.create.call_args.kwargs
    assert kwargs["model"] == "claude-sonnet-4-6"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_processor.py -v
```
Expected: `ModuleNotFoundError: No module named 'processor'`

- [ ] **Step 3: Implement processor.py**

Create `processor.py`:
```python
from anthropic import Anthropic

MAIL_PROMPT = (
    "Formuliere den folgenden diktierten Text als professionelle, prägnante E-Mail auf Deutsch um. "
    "Behalte den Inhalt bei, verbessere Struktur und Ton."
)
RAGE_PROMPT = (
    "Formuliere den folgenden Text humorvoll und übertrieben dramatisch um, "
    "als wäre der Autor sehr frustriert. Halte es auf Deutsch, kreativ und unterhaltsam."
)
_MODEL = "claude-sonnet-4-6"


def process_mail(text: str, config: dict) -> str:
    return _call_claude(text, MAIL_PROMPT, config)


def process_rage(text: str, config: dict) -> str:
    return _call_claude(text, RAGE_PROMPT, config)


def _call_claude(text: str, system_prompt: str, config: dict) -> str:
    client = Anthropic(api_key=config["anthropic_api_key"])
    response = client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": text}],
    )
    return response.content[0].text
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_processor.py -v
```
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add processor.py tests/test_processor.py
git commit -m "feat: Claude processor for mail and rage modes"
```

---

### Task 8: tray.py — system tray icon

**Files:**
- Create: `tray.py`

No unit tests — pystray/Pillow GUI not testable headlessly. Verified in Task 10.

- [ ] **Step 1: Implement tray.py**

Create `tray.py`:
```python
import threading
import tkinter as tk
from PIL import Image, ImageDraw
import pystray


def _create_icon_image() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill="#4a9eff")
    draw.ellipse([20, 20, 44, 44], fill="white")
    return img


class TrayApp:
    def __init__(self, root: tk.Tk, on_settings: callable, on_quit: callable):
        self._root = root
        self._on_settings = on_settings
        self._on_quit = on_quit
        self._icon: pystray.Icon | None = None

    def run(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem("Einstellungen", self._open_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Beenden", self._quit),
        )
        self._icon = pystray.Icon(
            "Blitztext",
            _create_icon_image(),
            "Blitztext",
            menu,
        )
        thread = threading.Thread(target=self._icon.run, daemon=True)
        thread.start()

    def _open_settings(self, icon=None, item=None) -> None:
        self._root.after(0, self._on_settings)

    def _quit(self, icon=None, item=None) -> None:
        if self._icon:
            self._icon.stop()
        self._root.after(0, self._on_quit)
```

- [ ] **Step 2: Commit**

```bash
git add tray.py
git commit -m "feat: pystray system tray with settings and quit menu"
```

---

### Task 9: settings.py — SettingsWindow UI

**Files:**
- Modify: `settings.py` (append SettingsWindow class)

- [ ] **Step 1: Append SettingsWindow to settings.py**

Add to the bottom of `settings.py`:
```python
import tkinter as tk
from tkinter import ttk


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
```

- [ ] **Step 2: Run full test suite to verify no regressions**

```bash
pytest tests/ -v
```
Expected: all existing tests PASS

- [ ] **Step 3: Commit**

```bash
git add settings.py
git commit -m "feat: SettingsWindow tkinter UI with all config fields"
```

---

### Task 10: main.py — wire everything together

**Files:**
- Create: `main.py`

- [ ] **Step 1: Implement main.py**

Create `main.py`:
```python
import sys
import threading
import time
import tkinter as tk

import keyboard

from overlay import Overlay
from recorder import AudioRecorder
from settings import load_config, save_config, SettingsWindow
from tray import TrayApp
import transcriber
import processor
import injector


class BlitzText:
    def __init__(self):
        self._config = load_config()
        self._recorder = AudioRecorder()
        self._active_mode: str | None = None

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
        if self._active_mode:
            return
        labels = {"transcribe": "🎙️ Transkription", "mail": "🎙️ Mail-Modus", "rage": "🎙️ Rage-Modus"}
        self._active_mode = mode
        try:
            self._recorder.start()
        except Exception:
            self._overlay.show("❌ Kein Mikrofon gefunden")
            self._active_mode = None
            return
        self._overlay.show(f"{labels[mode]}...", persistent=True)

    def _stop_mode(self, mode: str) -> None:
        if self._active_mode != mode:
            return
        self._active_mode = None
        self._overlay.update_message("⏳ Wird verarbeitet...")
        threading.Thread(target=self._process, args=(mode,), daemon=True).start()

    def _process(self, mode: str) -> None:
        audio_path = self._recorder.stop()
        if not audio_path:
            self._overlay.show("❌ Keine Aufnahme")
            return

        openai_key = self._config.get("openai_api_key", "")
        if not openai_key:
            self._overlay.hide()
            self._root.after(0, self._settings_window.open)
            return

        try:
            text = transcriber.transcribe(audio_path, self._config)
        except Exception:
            self._overlay.show("❌ Fehler: API nicht erreichbar")
            return

        if mode in ("mail", "rage"):
            anthropic_key = self._config.get("anthropic_api_key", "")
            if not anthropic_key:
                self._overlay.hide()
                self._root.after(0, self._settings_window.open)
                return
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
        hotkeys = self._config["hotkeys"]
        state: dict[str, bool] = {mode: False for mode in hotkeys}
        while True:
            for mode, hotkey in hotkeys.items():
                pressed = keyboard.is_pressed(hotkey)
                if pressed and not state[mode]:
                    state[mode] = True
                    threading.Thread(target=self._start_mode, args=(mode,), daemon=True).start()
                elif not pressed and state[mode]:
                    state[mode] = False
                    threading.Thread(target=self._stop_mode, args=(mode,), daemon=True).start()
            time.sleep(0.05)

    def run(self) -> None:
        self._tray.run()
        hotkey_thread = threading.Thread(target=self._hotkey_listener, daemon=True)
        hotkey_thread.start()
        self._root.mainloop()


if __name__ == "__main__":
    app = BlitzText()
    app.run()
```

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v
```
Expected: all tests PASS

- [ ] **Step 3: Smoke test — start the app**

```bash
python main.py
```

Expected:
- No console errors
- Tray icon appears in system tray (bottom-right taskbar)
- Right-click on tray icon shows "Einstellungen" and "Beenden"
- "Einstellungen" opens settings window with all fields
- Enter API keys and save → `config.json` created in project folder
- Hold `Ctrl+Alt+Space` → overlay appears top-right with "🎙️ Transkription..."
- Release → overlay shows "⏳ Wird verarbeitet..." then "✓ Fertig"
- Text appears at cursor position

- [ ] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: main entry point wiring all modules with hotkey polling loop"
```

---

### Task 11: README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README.md**

Create `README.md`:
```markdown
# Blitztext für Windows

Systemweites Sprach-Diktat per Hotkey in jede beliebige Anwendung.

## Voraussetzungen

- Python 3.11+
- Mikrofon
- OpenAI API Key (für Transkription via Whisper)
- Anthropic API Key (für Mail- und Rage-Modus, optional)

## Installation

```bash
pip install -r requirements.txt
```

## Starten

> **Wichtig:** Für globale Hotkeys (auch wenn ein anderes Fenster im Fokus ist) muss die App mit **Administratorrechten** gestartet werden.

Rechtsklick auf `main.py` → "Als Administrator ausführen", oder:

```bash
# In einer Admin-PowerShell:
python main.py
```

Beim ersten Start öffnet sich automatisch das Einstellungsfenster.

## Bedienung

| Hotkey | Funktion |
|--------|----------|
| `Ctrl+Alt+Space` | Transkription (unverändert) |
| `Ctrl+Alt+M` | Mail-Modus (via Claude umformuliert) |
| `Ctrl+Alt+R` | Rage-Modus (humorvoll-sarkastisch via Claude) |

Hotkey **gedrückt halten** → sprechen → **loslassen** → Text wird eingefügt.

## Einstellungen

Rechtsklick auf das Tray-Icon → **Einstellungen**

- OpenAI API Key (Whisper)
- Anthropic API Key (Claude, für Mail- und Rage-Modus)
- Hotkeys anpassen
- Whisper Sprache und Modell
- Autostart mit Windows

## Projektstruktur

```
blitztext/
├── main.py          # Einstiegspunkt
├── recorder.py      # Audioaufnahme
├── transcriber.py   # Whisper API
├── processor.py     # Claude API (Mail + Rage)
├── injector.py      # Text einfügen via Clipboard
├── overlay.py       # Feedback-Overlay
├── tray.py          # System Tray
├── settings.py      # Einstellungen UI + config.json
├── config.json      # Wird beim ersten Start erstellt
└── requirements.txt
```
```

- [ ] **Step 2: Final commit**

```bash
git add README.md
git commit -m "docs: README with installation, hotkeys, and admin rights note"
```

---

## Self-Review

**Spec coverage check:**
- ✅ Systemweit im Hintergrund als Tray-App → `tray.py`, `main.py`
- ✅ Hotkey gedrückt halten → Aufnahme → Loslassen → API → Einfügen → `main.py` `_hotkey_listener`
- ✅ Transkriptions-Modus `ctrl+alt+space` → `_process` mode=transcribe
- ✅ Mail-Modus `ctrl+alt+m` → `processor.process_mail`
- ✅ Rage-Modus `ctrl+alt+r` → `processor.process_rage`
- ✅ Mail System-Prompt auf Deutsch → `MAIL_PROMPT` in `processor.py`
- ✅ Rage System-Prompt → `RAGE_PROMPT` in `processor.py`
- ✅ Overlay oben rechts, halbtransparent, 2s nach Abschluss → `overlay.py`
- ✅ Overlay zeigt Modus, Status, Fertig → `_start_mode`, `_stop_mode`, `_process`
- ✅ Tray-Icon mit Menü → `tray.py`
- ✅ Settings: alle Felder → `SettingsWindow`
- ✅ config.json → `settings.py` `load_config`/`save_config`
- ✅ Kein GUI-Hauptfenster → `root.withdraw()`
- ✅ Clipboard-Einfügen mit Wiederherstellung → `injector.py`
- ✅ Temp WAV löschen → `transcriber.py`
- ✅ Fehlender API Key → Settings öffnen → `_process`
- ✅ API-Fehler → Overlay → `_process` except-Blöcke
- ✅ Kein Mikrofon → Overlay → `_start_mode` except
- ✅ Adminrechte-Hinweis → `README.md`
- ✅ Autostart-Einstellung → `SettingsWindow` (UI only; actual Windows registry hookup not in spec)
