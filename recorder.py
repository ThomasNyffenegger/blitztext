import os
import time
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav


class AudioRecorder:
    SAMPLE_RATE = 16000
    CHANNELS = 1
    MIN_SECONDS = 0.5  # ignore recordings shorter than this

    def __init__(self):
        self._recording = False
        self._frames = []
        self._stream = None
        self._start_time: float = 0.0

    def start(self) -> None:
        self._frames = []
        self._recording = True
        self._start_time = time.monotonic()
        self._stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype="int16",
            callback=self._callback,
        )
        self._stream.start()

    def _callback(self, indata, frames, time, status):
        if self._recording:
            self._frames.append(indata.copy())

    def stop(self) -> str | None:
        self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        duration = time.monotonic() - self._start_time
        if not self._frames or duration < self.MIN_SECONDS:
            return None
        audio = np.concatenate(self._frames, axis=0)
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_audio.wav")
        wav.write(path, self.SAMPLE_RATE, audio)
        return path

    @property
    def is_recording(self) -> bool:
        return self._recording
