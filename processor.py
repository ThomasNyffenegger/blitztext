from anthropic import Anthropic

MAIL_PROMPT = (
    "Formuliere den folgenden diktierten Text als professionelle, prägnante E-Mail auf Deutsch um. "
    "Behalte den Inhalt bei, verbessere Struktur und Ton."
)
RAGE_PROMPT = (
    "Formuliere den folgenden Text humorvoll und übertrieben dramatisch um, "
    "als wäre der Autor sehr frustriert. Halte es auf Deutsch, kreativ und unterhaltsam."
)
_MODEL = "claude-sonnet-4-6"


def process_mail(text: str, config: dict) -> str:
    return _call_claude(text, MAIL_PROMPT, config)


def process_rage(text: str, config: dict) -> str:
    return _call_claude(text, RAGE_PROMPT, config)


def _call_claude(text: str, system_prompt: str, config: dict) -> str:
    client = Anthropic(api_key=config["anthropic_api_key"])
    response = client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": text}],
    )
    return response.content[0].text
