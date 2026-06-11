import os

import numpy as np
import scipy.io.wavfile as wav
from tqdm import tqdm
from faster_whisper import WhisperModel
import faster_whisper.utils as fw_utils
from huggingface_hub import snapshot_download

# Lokal geladene Modelle (faster-whisper / CTranslate2), gecacht im RAM
_model_cache: dict[str, WhisperModel] = {}

# int8 ist auf der CPU am schnellsten; gleiche Genauigkeit wie openai-whisper
_DEVICE = "cpu"
_COMPUTE_TYPE = "int8"


class DownloadCancelled(Exception):
    """Raised when a model download is cancelled by the user."""


def _repo_id(model_name: str) -> str:
    return fw_utils._MODELS.get(model_name, model_name)


def is_model_downloaded(model_name: str) -> bool:
    """True if the model is already present in the local HuggingFace cache."""
    try:
        snapshot_download(_repo_id(model_name), local_files_only=True)
        return True
    except Exception:
        return False


def download_model(model_name: str, progress_cb=None, cancel_event=None) -> None:
    """Download a model from HuggingFace with progress reporting and cancellation.

    progress_cb: called with (downloaded_bytes, total_bytes) during download.
    cancel_event: a threading.Event; if set, aborts and raises DownloadCancelled.

    Note: HuggingFace lädt mehrere Dateien; die große model.bin dominiert die Anzeige.
    """
    if is_model_downloaded(model_name):
        return

    class _CancellableTqdm(tqdm):
        def update(self, n=1):
            if cancel_event is not None and cancel_event.is_set():
                raise DownloadCancelled()
            super().update(n)
            if progress_cb and self.total:
                progress_cb(self.n, self.total)

    snapshot_download(_repo_id(model_name), tqdm_class=_CancellableTqdm)


def preload_model(model_name: str) -> None:
    if model_name not in _model_cache:
        _model_cache[model_name] = WhisperModel(
            model_name, device=_DEVICE, compute_type=_COMPUTE_TYPE
        )


def is_model_loaded(model_name: str) -> bool:
    return model_name in _model_cache


def transcribe(audio_path: str, config: dict, task: str = "transcribe") -> str:
    """Transcribe (task="transcribe") or translate to English (task="translate")."""
    model_name = config.get("whisper_model", "small")
    preload_model(model_name)

    # Load audio with scipy to avoid an ffmpeg dependency
    sample_rate, audio_int16 = wav.read(audio_path)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0
    if audio_float32.ndim > 1:
        audio_float32 = audio_float32.mean(axis=1)

    try:
        os.remove(audio_path)
    except OSError:
        pass

    segments, _info = _model_cache[model_name].transcribe(
        audio_float32,
        language=config.get("whisper_language", "de"),
        task=task,
    )
    return "".join(segment.text for segment in segments)
