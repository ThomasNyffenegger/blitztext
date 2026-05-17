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
