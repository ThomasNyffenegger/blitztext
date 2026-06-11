"""Misst den Real-Time-Factor (RTF) der Whisper-Modelle auf dieser Maschine.

Zweck: feststellen, ob auf einer schnelleren CPU eine Live-Transkription
(Streaming) machbar ist. Siehe docs/streaming-investigation.md.

RTF = Verarbeitungszeit / Audio-Dauer.
  RTF < 1   = schneller als Echtzeit
  RTF < 0,5 = Faustregel, ab der echtes Streaming sinnvoll wird
              (überlappende Fenster werden mehrfach transkribiert)

Wichtig: Der "5s-Fenster"-Wert ist der für Streaming entscheidende, weil
mittendrin abgeschnittenes Audio den Decoder zu Halluzinations-Schleifen
bringt – genau das, was Streaming permanent erzeugt.

Aufruf:
    python benchmark_rtf.py

Voraussetzungen: faster-whisper, scipy, numpy (siehe requirements.txt).
Erzeugt eine kurze deutsche Sprachprobe via Windows-TTS (System.Speech).
"""

import subprocess
import sys
import time
import os

import numpy as np
import scipy.io.wavfile as wav
import scipy.signal as sig
from faster_whisper import WhisperModel

SAMPLE_TEXT = (
    "Dies ist ein etwas laengerer Testsatz um die Geschwindigkeit der "
    "Transkription bei verschiedenen Modellgroessen realistisch zu messen."
)
WAV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_bench_tmp.wav")
MODELS = ["tiny", "base", "small"]


def make_sample() -> None:
    """Erzeugt eine deutsche Sprachprobe via Windows-TTS."""
    ps = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$s.SetOutputToWaveFile('{WAV_PATH}'); "
        f"$s.Speak('{SAMPLE_TEXT}'); $s.Dispose()"
    )
    subprocess.run(["powershell", "-Command", ps], check=True)


def load_audio() -> np.ndarray:
    sr, data = wav.read(WAV_PATH)
    audio = sig.resample(data.astype(np.float32), int(len(data) * 16000 / sr))
    return audio.astype(np.float32)


def time_transcribe(model: WhisperModel, audio: np.ndarray, runs: int) -> float:
    times = []
    for _ in range(runs):
        t0 = time.time()
        list(model.transcribe(audio, language="de")[0])
        times.append(time.time() - t0)
    return sum(times) / len(times)


def main() -> None:
    print("Erzeuge Sprachprobe …")
    make_sample()
    audio = load_audio()
    dur = len(audio) / 16000
    window = audio[: int(5 * 16000)]  # mittendrin abgeschnittenes 5s-Fenster
    print(f"Audio: {dur:.1f}s gesamt, Streaming-Fenster: 5.0s\n")
    print(f"{'Modell':<8} {'Fenster(5s)':<16} {'Voll':<16}")
    print("-" * 40)

    for size in MODELS:
        model = WhisperModel(size, device="cpu", compute_type="int8", num_workers=1)
        for _ in range(3):  # warmup
            list(model.transcribe(window, language="de")[0])
        w = time_transcribe(model, window, runs=5)
        f = time_transcribe(model, audio, runs=3)
        print(f"{size:<8} {w:.2f}s RTF {w/5:<5.2f}  {f:.2f}s RTF {f/dur:<5.2f}")
        del model

    try:
        os.remove(WAV_PATH)
    except OSError:
        pass

    print("\nFaustregel: Streaming lohnt sich, wenn der Fenster-RTF < 0,5 liegt.")
    print("Auf dem Entwicklungs-Laptop (GTX 960M, Haswell-CPU) lag tiny im")
    print("Fenster-Fall stabil bei RTF ~1,5-1,9 -> Streaming NICHT machbar.")


if __name__ == "__main__":
    main()
