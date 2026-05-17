import os
from openai import OpenAI


def transcribe(audio_path: str, config: dict) -> str:
    client = OpenAI(api_key=config["openai_api_key"])
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model=config.get("whisper_model", "whisper-1"),
            file=f,
            language=config.get("whisper_language", "de"),
        )
    os.remove(audio_path)
    return result.text
