import time
import pyperclip
import keyboard


def inject_text(text: str) -> None:
    try:
        original = pyperclip.paste()
    except Exception:
        original = ""

    pyperclip.copy(text)
    time.sleep(0.15)
    keyboard.send("ctrl+v")
    time.sleep(0.15)
    pyperclip.copy(original)
