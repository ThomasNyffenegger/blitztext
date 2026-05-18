from unittest.mock import patch, call


def test_inject_text_pastes_text():
    with patch("injector.pyperclip.paste", return_value="original"), \
         patch("injector.pyperclip.copy") as mock_copy, \
         patch("injector.keyboard.send") as mock_send, \
         patch("injector.time.sleep"):
        from injector import inject_text
        inject_text("injizierter Text")
    mock_send.assert_called_once_with("ctrl+v")
    assert mock_copy.call_args_list[0] == call("injizierter Text")


def test_inject_text_restores_clipboard():
    with patch("injector.pyperclip.paste", return_value="Originalinhalt"), \
         patch("injector.pyperclip.copy") as mock_copy, \
         patch("injector.keyboard.send"), \
         patch("injector.time.sleep"):
        from injector import inject_text
        inject_text("neuer Text")
    assert mock_copy.call_args_list[-1] == call("Originalinhalt")


def test_inject_text_handles_empty_clipboard():
    with patch("injector.pyperclip.paste", side_effect=Exception("no clipboard")), \
         patch("injector.pyperclip.copy") as mock_copy, \
         patch("injector.keyboard.send"), \
         patch("injector.time.sleep"):
        from injector import inject_text
        inject_text("Text")
    assert mock_copy.call_args_list[0] == call("Text")
    assert mock_copy.call_args_list[-1] == call("")
