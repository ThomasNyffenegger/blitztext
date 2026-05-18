import os
import whisper

_model_cache: dict[str, whisper.Whisper] = {}


def preload_model(model_name: str) -> None:
    if model_name not in _model_cache:
        _model_cache[model_name] = whisper.load_model(model_name)


def is_model_loaded(model_name: str) -> bool:
    return model_name in _model_cache


def transcribe(audio_path: str, config: dict) -> str:
    model_name = config.get("whisper_model", "base")
    preload_model(model_name)
    result = _model_cache[model_name].transcribe(
        audio_path, language=config.get("whisper_language", "de")
    )
    try:
        os.remove(audio_path)
    except OSError:
        pass
    return result["text"]
