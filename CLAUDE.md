# Blitztext für Windows – Projektkontext

## Was ist das?
Blitztext ist eine Windows-Desktop-App, die systemweites Sprach-Diktat per Hotkey in jede beliebige Anwendung ermöglicht. Inspiriert von einer Mac-App des deutschen YouTubers Christoph Magnussen. Transkription via lokalem openai-whisper, Textverarbeitung via Anthropic Claude API.

## Wichtigste Designentscheidungen
- **Kein GUI-Hauptfenster** – die App lebt im System Tray
- **Transkription lokal** via `openai-whisper` (kein OpenAI API Key nötig, kein Internet für Diktat)
- **Text-Einfügen via Clipboard** (`ctypes.windll.user32.keybd_event` simuliert Ctrl+V) – zuverlässiger als pyautogui bei Sonderzeichen und Umlauten
- **Clipboard-Verifikationsschleife** vor dem Einfügen: wartet bis pyperclip.paste() == text (bis 1s), um Kaspersky-bedingte Clipboard-Verzögerungen abzufangen
- **Zwischenablage wiederherstellen** nach dem Einfügen
- **Globale Hotkeys** erfordern Adminrechte unter Windows
- **Kein blocking** – Aufnahme, Transkription und Einfügen laufen in separaten Threads
- **Autostart** via Windows-Registry (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`)
- **Mindestaufnahmedauer** 0.5s – kürzere Aufnahmen werden ignoriert
- **Modell-Caching** – Whisper-Modell bleibt nach erstem Laden im RAM

## Fehlerbehandlung
- Fehlender Anthropic API Key → Einstellungs-Fenster öffnet sich automatisch
- Fehler bei Transkription/API → Overlay zeigt `❌ Fehler: <ExceptionType>`
- Kein Mikrofon erkannt → Overlay zeigt `❌ Kein Mikrofon gefunden`
- Leere Transkription → Overlay zeigt `❌ Nichts erkannt – länger sprechen`
- Niemals Pop-up-Dialoge für Fehler – immer Overlay

## Sprache
- App-UI auf Deutsch
- Whisper-Spracheinstellung Standard: `de`
- Claude API System-Prompts auf Deutsch

## Projektstruktur
```
blitztext/
├── main.py          # Einstiegspunkt, Hotkey-Listener, Threading
├── recorder.py      # Audioaufnahme (sounddevice, 16kHz, int16)
├── transcriber.py   # Transkription (openai-whisper, lokal, scipy WAV-Loading)
├── processor.py     # Textverarbeitung (Claude API, Mail + Rage)
├── injector.py      # Text einfügen via Clipboard + ctypes Ctrl+V
├── overlay.py       # Feedback-Overlay (tkinter)
├── tray.py          # System Tray Icon + Menü (pystray)
├── settings.py      # Einstellungen UI, config.json, Autostart-Registry
├── config.json      # Wird beim ersten Start erstellt
├── install.bat      # Einmalige Installation der Abhängigkeiten
├── requirements.txt
└── tests/           # pytest-Testsuite (19 Tests)
```

## config.json Struktur (Standardwerte)
```json
{
  "anthropic_api_key": "",
  "whisper_model": "small",
  "whisper_language": "de",
  "autostart": false,
  "hotkeys": {
    "transcribe": "ctrl+shift+y",
    "mail": "ctrl+alt+m",
    "rage": "ctrl+alt+r"
  }
}
```

## Bekannte Eigenheiten
- **Kaspersky** verzögert Clipboard-Zugriffe um bis zu ~500ms → Verifikationsschleife in `injector.py` fängt das ab
- **PyTorch CUDA** nicht nutzbar auf Python 3.14 (keine Wheels verfügbar) → CPU-Inferenz, ~3s für kurze Diktate mit `small`-Modell
- **scipy** wird zum WAV-Laden verwendet (nicht ffmpeg), um eine externe Abhängigkeit zu vermeiden
- `openai_api_key` im Einstellungs-UI nicht mehr vorhanden, da Transkription lokal läuft
