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
