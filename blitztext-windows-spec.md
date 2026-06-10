# Blitztext für Windows – Funktionsbeschrieb

Baue eine Windows-Desktop-App namens **Blitztext** in Python. Die App läuft im Hintergrund als System-Tray-Anwendung und ermöglicht es, per Hotkey in jede beliebige Anwendung zu diktieren. Die Transkription erfolgt über die OpenAI Whisper API.

---

## Kernfunktion

- Die App startet beim Systemstart und läuft unsichtbar im Hintergrund (System Tray Icon)
- Der Nutzer drückt einen konfigurierbaren Hotkey, spricht, lässt den Hotkey los
- Die Aufnahme wird an die OpenAI Whisper API geschickt
- Der transkribierte Text wird automatisch an der aktuellen Cursor-Position eingefügt (als wäre er getippt worden) – in jeder beliebigen App (Outlook, Teams, Browser, etc.)

---

## Modi / Hotkeys

Drei verschiedene Verarbeitungsmodi, jeder mit eigenem Hotkey (konfigurierbar):

### 1. Transkriptions-Modus (`Ctrl+Alt+Space`)
- Nimmt Sprache auf, solange der Hotkey gehalten wird
- Schickt Audio an Whisper API
- Fügt den transkribierten Text **unverändert** am Cursor ein
- Ideal für: schnelles Diktieren, Chats, Notizen

### 2. Mail-Modus (`Ctrl+Alt+M`)
- Nimmt Sprache auf, solange der Hotkey gehalten wird
- Schickt Audio an Whisper API für Transkription
- Sendet den transkribierten Text anschliessend an die Anthropic Claude API mit dem System-Prompt: *„Formuliere den folgenden diktierten Text als professionelle, prägnante E-Mail auf Deutsch um. Behalte den Inhalt bei, verbessere Struktur und Ton."*
- Fügt den umformulierten Text am Cursor ein
- Ideal für: Outlook, Gmail, Teams-Nachrichten

### 3. Rage-Modus (`Ctrl+Alt+R`)
- Wie der Transkriptions-Modus, aber Claude formuliert den Text humorvoll-sarkastisch um, als hätte man gerade einen sehr schlechten Tag
- Rein zur Unterhaltung – Nutzer prüft den Text vor dem Senden selbst
- System-Prompt: *„Formuliere den folgenden Text humorvoll und übertrieben dramatisch um, als wäre der Autor sehr frustriert. Halte es auf Deutsch, kreativ und unterhaltsam."*

---

## Visuelles Feedback

- Kleines, dezentes Overlay-Fenster (oben rechts im Bildschirm, halbtransparent):
  - Zeigt an, welcher Modus aktiv ist (z.B. 🎙️ Transkription...)
  - Zeigt den Status: „Aufnahme läuft", „Wird verarbeitet...", „Fertig ✓"
  - Verschwindet automatisch nach 2 Sekunden nach Abschluss
- System Tray Icon mit rechter Maustaste für Einstellungen und Beenden

---

## Einstellungen (einfaches Settings-Fenster über Tray-Icon)

- OpenAI API Key (für Whisper)
- Anthropic API Key (für Mail- und Rage-Modus)
- Hotkeys anpassen (alle drei Modi)
- Sprache für Whisper (Standard: `de`)
- Autostart mit Windows: ja/nein
- Whisper-Modell: `whisper-1` (Standard)

Einstellungen werden in einer lokalen `config.json` gespeichert.

---

## Technischer Stack

- **Python 3.11+**
- `keyboard` – globale Hotkeys (systemweit, auch wenn App nicht im Fokus)
- `sounddevice` + `scipy` – Audioaufnahme vom Mikrofon
- `openai` – Whisper API für Transkription
- `anthropic` – Claude API für Mail- und Rage-Modus
- `pyperclip` + `pyautogui` – Text in aktives Fenster einfügen
- `pystray` + `Pillow` – System Tray Icon
- `tkinter` – Overlay-Fenster und Einstellungs-UI

---

## Projektstruktur

```
blitztext/
├── main.py              # Einstiegspunkt, startet Tray + Hotkey-Listener
├── recorder.py          # Audioaufnahme (sounddevice)
├── transcriber.py       # Whisper API Call
├── processor.py         # Claude API Calls (Mail-Modus, Rage-Modus)
├── injector.py          # Text in aktives Fenster einfügen
├── overlay.py           # Visuelles Feedback-Overlay (tkinter)
├── tray.py              # System Tray Icon + Menü
├── settings.py          # Einstellungs-Fenster + config.json lesen/schreiben
├── config.json          # API Keys, Hotkeys, Sprache (wird beim ersten Start erstellt)
└── requirements.txt
```

---

## Wichtige Hinweise für die Implementierung

- Hotkeys müssen **global** funktionieren (auch wenn ein anderes Fenster im Fokus ist)
- Das Einfügen des Textes soll über die Zwischenablage + `Ctrl+V` geschehen (zuverlässigste Methode unter Windows), die ursprüngliche Zwischenablage danach wiederherstellen
- Die App soll robust gegen fehlende API Keys sein: bei fehlendem Key öffnet sich automatisch das Einstellungs-Fenster
- Audio wird als temporäre `.wav`-Datei gespeichert, nach der Transkription sofort gelöscht
- Fehler (API nicht erreichbar, kein Mikrofon) werden als kurze Overlay-Meldung angezeigt, nicht als Pop-up-Dialog
