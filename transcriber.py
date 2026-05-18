import os
import whisper

_model_cache: dict[str, whisper.Whisper] = {}


def transcribe(audio_path: str, config: dict) -> str:
    model_name = config.get("whisper_model", "base")
    if model_name not in _model_cache:
        _model_cache[model_name] = whisper.load_model(model_name)
    model = _model_cache[model_name]
    result = model.transcribe(audio_path, language=config.get("whisper_language", "de"))
    try:
        os.remove(audio_path)
    except OSError:
        pass
    return result["text"]
