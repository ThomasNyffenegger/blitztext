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
