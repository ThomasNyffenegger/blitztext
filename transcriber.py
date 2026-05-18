import os
import numpy as np
import scipy.io.wavfile as wav
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

    # Load audio with scipy to avoid ffmpeg dependency
    sample_rate, audio_int16 = wav.read(audio_path)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0
    if audio_float32.ndim > 1:
        audio_float32 = audio_float32.mean(axis=1)

    try:
        os.remove(audio_path)
    except OSError:
        pass

    result = _model_cache[model_name].transcribe(
        audio_float32, language=config.get("whisper_language", "de")
    )
    return result["text"]
