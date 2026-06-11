"""Reine Logik für die Diktat-Modi – ohne UI/Threading, damit testbar."""

import processor

MODE_LABELS = {
    "transcribe": "🎙️ Transkription",
    "translate": "🎙️ Übersetzung → EN",
    "mail": "🎙️ Mail-Modus",
    "rage": "🎙️ Rage-Modus",
}

# Modi, die nach der Transkription noch durch Claude laufen
CLAUDE_MODES = ("mail", "rage")


def mode_label(mode: str) -> str:
    return MODE_LABELS.get(mode, mode)


def whisper_task_for(mode: str) -> str:
    """Whisper-Task: translate übersetzt nach Englisch, sonst wörtliche Transkription."""
    return "translate" if mode == "translate" else "transcribe"


def needs_claude(mode: str) -> bool:
    return mode in CLAUDE_MODES


def apply_claude(mode: str, text: str, config: dict) -> str:
    """Wendet den passenden Claude-Prozessor an. Unbekannte Modi geben den Text unverändert zurück."""
    if mode == "mail":
        return processor.process_mail(text, config)
    if mode == "rage":
        return processor.process_rage(text, config)
    return text
