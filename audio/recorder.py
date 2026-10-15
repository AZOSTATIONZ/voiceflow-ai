import logging
import threading

import numpy as np
import sounddevice as sd

log = logging.getLogger(__name__)
SAMPLE_RATE = 16000


def list_input_devices() -> list[tuple[int, str]]:
    out = []
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0 and sd.query_hostapis(d["hostapi"])["name"] == "MME":
            out.append((i, d["name"]))
    return out


class Recorder:
    """Captures 16 kHz mono float32 audio between start() and stop()."""

    def __init__(self):
        self._chunks: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()

    def start(self, device: int | None = None) -> None:
        with self._lock:
            if self._stream:
                return
            self._chunks = []
            self._stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                                          device=device, callback=self._callback)
            self._stream.start()

    def _callback(self, indata, frames, time_info, status):
        if status:
            log.debug("audio status: %s", status)
        self._chunks.append(indata[:, 0].copy())

    def stop(self) -> np.ndarray:
        with self._lock:
            if not self._stream:
                return np.zeros(0, dtype=np.float32)
            self._stream.stop()
            self._stream.close()
            self._stream = None
            if not self._chunks:
                return np.zeros(0, dtype=np.float32)
            return np.concatenate(self._chunks)

    @property
    def active(self) -> bool:
        return self._stream is not None
