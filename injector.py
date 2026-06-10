import ctypes
import time
import pyperclip

_VK_CONTROL = 0x11
_VK_V = 0x56
_KEYEVENTF_KEYUP = 0x0002


def _ctrl_v() -> None:
    ke = ctypes.windll.user32.keybd_event
    ke(_VK_CONTROL, 0, 0, 0)
    ke(_VK_V, 0, 0, 0)
    time.sleep(0.05)
    ke(_VK_V, 0, _KEYEVENTF_KEYUP, 0)
    ke(_VK_CONTROL, 0, _KEYEVENTF_KEYUP, 0)


def inject_text(text: str) -> None:
    try:
        original = pyperclip.paste()
    except Exception:
        original = ""

    pyperclip.copy(text)

    # Wait until clipboard actually contains our text (Kaspersky may delay)
    for _ in range(20):
        time.sleep(0.05)
        try:
            if pyperclip.paste() == text:
                break
        except Exception:
            pass

    _ctrl_v()
    time.sleep(0.2)
    pyperclip.copy(original)
