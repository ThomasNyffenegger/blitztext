# Blitztext für Windows

Systemweites Sprach-Diktat per Hotkey in jede beliebige Anwendung.

## Voraussetzungen

- Python 3.11+
- Mikrofon
- Anthropic API Key (optional, nur für Mail- und Rage-Modus)

Transkription läuft lokal via [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — kein API-Key nötig, offline nach dem einmaligen Modell-Download. Beim ersten Start wird das Whisper-Modell (`small`, ~480MB) automatisch vom HuggingFace Hub geladen. faster-whisper ist auf der CPU rund 2× schneller als openai-whisper bei gleicher Genauigkeit.

## Installation

```bash
pip install -r requirements.txt
```

Oder auf einem neuen PC: `install.bat` doppelklicken.

## Starten

> **Wichtig:** Für globale Hotkeys muss die App mit **Administratorrechten** gestartet werden.

Rechtsklick auf `main.py` → "Als Administrator ausführen", oder:

```powershell
# In einer Admin-PowerShell:
python main.py
```

## Bedienung

| Hotkey | Funktion |
|--------|----------|
| `Ctrl+Shift+Y` | Transkription (Text unverändert einfügen) |
| `Ctrl+Shift+E` | Übersetzung → Englisch (Deutsch sprechen, Englisch einfügen) |
| `Ctrl+Alt+M` | Mail-Modus (Claude formuliert als professionelle E-Mail um) |
| `Ctrl+Alt+R` | Rage-Modus (Claude macht aus Frust einen humorvollen Text) |

Hotkey **gedrückt halten** → sprechen → **loslassen** → Text erscheint an der Cursor-Position.

Hotkeys sind in den Einstellungen frei konfigurierbar.

## Einstellungen

Rechtsklick auf das Tray-Icon → **Einstellungen**

- Anthropic API Key (für Mail- und Rage-Modus)
- Whisper Modell (`tiny` / `base` / `small` / `medium`) und Sprache
- Hotkeys anpassen
- Autostart mit Windows

## Installation auf einem weiteren PC

1. Python 3.11+ installieren (python.org)
2. Diesen Ordner kopieren
3. `install.bat` doppelklicken
4. `python main.py` als Administrator starten

## Projektstruktur

```
blitztext/
├── main.py          # Einstiegspunkt, Hotkey-Listener, Threading
├── modes.py         # Modus-Routing (Transkription/Übersetzung/Mail/Rage)
├── recorder.py      # Audioaufnahme (sounddevice)
├── transcriber.py   # Transkription + Übersetzung (faster-whisper, lokal)
├── processor.py     # Textverarbeitung (Claude API, Mail + Rage)
├── injector.py      # Text einfügen via Clipboard + Ctrl+V
├── overlay.py       # Feedback-Overlay (tkinter)
├── tray.py          # System Tray Icon + Menü
├── settings.py      # Einstellungen UI, config.json, Autostart
├── config.json      # Wird beim ersten Start erstellt
├── install.bat      # Einmalige Installation der Abhängigkeiten
├── benchmark_rtf.py # Misst Whisper-Geschwindigkeit (Real-Time-Factor)
└── requirements.txt
```

## Geplant / Untersucht

- **Live-Transkription während des Sprechens** – untersucht, auf dem Entwicklungs-Laptop nicht machbar (CPU zu langsam für Echtzeit). Auf schnellerer Hardware erneut prüfen mit `python benchmark_rtf.py`. Details: [docs/streaming-investigation.md](docs/streaming-investigation.md).
