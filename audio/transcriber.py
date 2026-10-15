import logging
import os
import sys
import threading
from pathlib import Path

import numpy as np
import psutil

log = logging.getLogger(__name__)
CPU_THREADS = psutil.cpu_count(logical=False) or 4


def _cuda_dll_dirs() -> list[Path]:
    """Folders that may hold cuBLAS/cuDNN for CUDA 12: pip nvidia-* wheels, the CUDA toolkit, Ollama's bundle."""
    roots = [Path(p) for p in sys.path if p.endswith("site-packages")]
    if getattr(sys, "frozen", False):
        roots.append(Path(sys._MEIPASS))
    dirs = [d for r in roots for d in (r / "nvidia").glob("*/bin")]
    if os.environ.get("CUDA_PATH"):
        dirs.append(Path(os.environ["CUDA_PATH"]) / "bin")
    dirs.append(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Ollama/lib/ollama/cuda_v12")
    return [d for d in dirs if d.is_dir()]


def _enable_cuda_dlls() -> None:
    for d in _cuda_dll_dirs():
        os.add_dll_directory(str(d))
        os.environ["PATH"] = f"{d}{os.pathsep}{os.environ['PATH']}"


def _warm_up(model) -> None:
    segments, _ = model.transcribe(np.zeros(16000, dtype=np.float32), language="en", beam_size=1)
    list(segments)


def _create(name: str, device: str, compute_type: str):
    """Use the cached model offline; only hit the network when it hasn't been downloaded yet."""
    from faster_whisper import WhisperModel
    kw = dict(device=device, compute_type=compute_type, cpu_threads=CPU_THREADS)
    try:
        return WhisperModel(name, local_files_only=True, **kw)
    except Exception:
        log.info("downloading whisper model %s", name)
        return WhisperModel(name, **kw)


class Transcriber:
    """Local speech-to-text with faster-whisper. The model loads lazily and is cached."""

    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    def set_model(self, name: str) -> None:
        with self._lock:
            if name != self.model_name:
                self.model_name = name
                self._model = None

    def load(self):
        with self._lock:
            if self._model is None:
                import ctranslate2
                if ctranslate2.get_cuda_device_count() > 0:
                    _enable_cuda_dlls()
                    try:
                        model = _create(self.model_name, "cuda", "int8_float16")
                        _warm_up(model)  # CUDA libs (cuBLAS/cuDNN) only fail at first inference
                        self._model = model
                        log.info("whisper %s loaded on CUDA", self.model_name)
                    except Exception as e:
                        log.info("CUDA unavailable (%s), using CPU", e)
                if self._model is None:
                    model = _create(self.model_name, "cpu", "int8")
                    _warm_up(model)
                    self._model = model
                    log.info("whisper %s loaded on CPU", self.model_name)
            return self._model

    def transcribe(self, audio: np.ndarray, language: str = "auto") -> str:
        if audio.size == 0:
            return ""
        model = self.load()
        segments, _ = model.transcribe(audio, language=None if language == "auto" else language,
                                       beam_size=1, vad_filter=True, condition_on_previous_text=False,
                                       without_timestamps=True)
        return " ".join(s.text.strip() for s in segments).strip()
