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
