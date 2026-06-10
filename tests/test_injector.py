from unittest.mock import patch, call, MagicMock


def _make_paste_side_effect(original: str, injected: str):
    """First call returns original clipboard; subsequent calls return injected text."""
    calls = [original]
    def side_effect():
        return calls.pop(0) if calls else injected
    return side_effect


def test_inject_text_pastes_text():
    mock_ke = MagicMock()
    with patch("injector.pyperclip.paste", side_effect=_make_paste_side_effect("original", "injizierter Text")), \
         patch("injector.pyperclip.copy") as mock_copy, \
         patch("injector.ctypes.windll.user32.keybd_event", mock_ke), \
         patch("injector.time.sleep"):
        from injector import inject_text
        inject_text("injizierter Text")
    assert mock_copy.call_args_list[0] == call("injizierter Text")
    assert mock_ke.called


def test_inject_text_restores_clipboard():
    with patch("injector.pyperclip.paste", side_effect=_make_paste_side_effect("Originalinhalt", "neuer Text")), \
         patch("injector.pyperclip.copy") as mock_copy, \
         patch("injector.ctypes.windll.user32.keybd_event"), \
         patch("injector.time.sleep"):
        from injector import inject_text
        inject_text("neuer Text")
    assert mock_copy.call_args_list[-1] == call("Originalinhalt")


def test_inject_text_handles_empty_clipboard():
    calls = {"n": 0}
    def paste_side_effect():
        calls["n"] += 1
        if calls["n"] == 1:
            raise Exception("no clipboard")
        return "Text"

    with patch("injector.pyperclip.paste", side_effect=paste_side_effect), \
         patch("injector.pyperclip.copy") as mock_copy, \
         patch("injector.ctypes.windll.user32.keybd_event"), \
         patch("injector.time.sleep"):
        from injector import inject_text
        inject_text("Text")
    assert mock_copy.call_args_list[0] == call("Text")
    assert mock_copy.call_args_list[-1] == call("")
