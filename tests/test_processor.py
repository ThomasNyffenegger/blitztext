from unittest.mock import MagicMock, patch
import processor as proc


CONFIG = {"anthropic_api_key": "test-key"}


def _mock_anthropic(response_text: str):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=response_text)]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    return mock_client


def test_process_mail_uses_mail_prompt():
    mock_client = _mock_anthropic("Sehr geehrte Damen und Herren...")
    with patch("processor.Anthropic", return_value=mock_client):
        result = proc.process_mail("hey schick mal die datei", CONFIG)
    assert result == "Sehr geehrte Damen und Herren..."
    kwargs = mock_client.messages.create.call_args.kwargs
    assert kwargs["system"] == proc.MAIL_PROMPT
    assert kwargs["messages"][0]["content"] == "hey schick mal die datei"


def test_process_rage_uses_rage_prompt():
    mock_client = _mock_anthropic("ICH BIN SO WÜTEND!!!")
    with patch("processor.Anthropic", return_value=mock_client):
        result = proc.process_rage("das meeting war langweilig", CONFIG)
    assert result == "ICH BIN SO WÜTEND!!!"
    kwargs = mock_client.messages.create.call_args.kwargs
    assert kwargs["system"] == proc.RAGE_PROMPT


def test_process_mail_uses_correct_model():
    mock_client = _mock_anthropic("E-Mail Text")
    with patch("processor.Anthropic", return_value=mock_client):
        proc.process_mail("text", CONFIG)
    kwargs = mock_client.messages.create.call_args.kwargs
    assert kwargs["model"] == "claude-sonnet-4-6"
