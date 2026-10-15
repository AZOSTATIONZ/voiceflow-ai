"""Dictation pipeline: hotkey -> record -> transcribe -> AI cleanup -> paste -> history."""
import logging
import threading
import time

from PySide6.QtCore import QObject, Signal

from ai.cleanup import Cleaner
from app.hotkey import HoldHotkey
from audio.recorder import SAMPLE_RATE, Recorder
from audio.transcriber import Transcriber
from context.detector import detect_context
from db.history import History
from utils.paste import insert_text

log = logging.getLogger(__name__)
MIN_SECONDS = 0.3


class Controller(QObject):
    state_changed = Signal(str)      # idle | listening | transcribing | cleaning | error
    message = Signal(str, str)       # title, body (tray notification)
    dictation_done = Signal(str)

    def __init__(self, store, history: History):
        super().__init__()
        self.store = store
        self.history = history
        self.recorder = Recorder()
        self.transcriber = Transcriber(store.settings.whisper_model)
        self.cleaner = Cleaner(store.settings)
        self.hotkey: HoldHotkey | None = None
        self._ctx = None
        self._prep: threading.Thread | None = None
        self._busy = threading.Lock()

    @property
    def settings(self):
        return self.store.settings

    def start(self) -> None:
        self._register_hotkey()
        threading.Thread(target=self._preload, daemon=True).start()

    def _preload(self) -> None:
        if self.settings.ai_cleanup:
            threading.Thread(target=self.cleaner.prewarm, daemon=True).start()
        try:
            self.transcriber.load()
        except Exception as e:
            log.exception("whisper load failed")
            self.message.emit("VoiceFlow AI", f"Could not load Whisper model: {e}")

    def _register_hotkey(self) -> None:
        if self.hotkey:
            self.hotkey.stop()
        try:
            self.hotkey = HoldHotkey(self.settings.hotkey, self.begin, self.end)
            self.hotkey.start()
        except Exception as e:
            log.exception("hotkey registration failed")
            self.message.emit("VoiceFlow AI", f"Invalid hotkey '{self.settings.hotkey}': {e}")

    def apply_settings(self) -> None:
        self.cleaner.settings = self.settings
        self.transcriber.set_model(self.settings.whisper_model)
        self._register_hotkey()
        threading.Thread(target=self._preload, daemon=True).start()

    def shutdown(self) -> None:
        if self.hotkey:
            self.hotkey.stop()
        self.recorder.stop()

    # -- pipeline -------------------------------------------------------------
    def toggle(self) -> None:
        """Tray 'Start Dictation': click once to start, again to stop."""
        if self.recorder.active:
            self.end()
        else:
            self.begin()

    def begin(self) -> None:
        if self._busy.locked() or self.recorder.active:
            return
        try:
            self.recorder.start(self.settings.mic_device)
            self.state_changed.emit("listening")
        except Exception as e:
            log.exception("microphone error")
            self.state_changed.emit("error")
            self.message.emit("Microphone error", str(e))
            return
        # While the user speaks: read context and warm the LLM so release -> paste is as short as possible.
        self._ctx = detect_context(read_text=False)
        self._prep = threading.Thread(target=self._prepare, args=(self._ctx,), daemon=True)
        self._prep.start()

    def _prepare(self, ctx) -> None:
        if self.settings.use_context:
            try:
                fresh = detect_context(read_text=True)
                if fresh.hwnd == ctx.hwnd:
                    ctx.text_before, ctx.text_after = fresh.text_before, fresh.text_after
            except Exception:
                log.debug("context read failed", exc_info=True)
        if self.settings.ai_cleanup:
            self.cleaner.prewarm(ctx)

    def end(self) -> None:
        if not self.recorder.active:
            return
        audio = self.recorder.stop()
        threading.Thread(target=self._process, args=(audio, self._ctx, self._prep), daemon=True).start()

    def _process(self, audio, ctx, prep=None) -> None:
        with self._busy:
            t0 = time.perf_counter()
            try:
                if audio.size < SAMPLE_RATE * MIN_SECONDS:
                    self.state_changed.emit("idle")
                    return
                self.state_changed.emit("transcribing")
                raw = self.transcriber.transcribe(audio, self.settings.language)
                log.info("raw (%.2fs): %s", time.perf_counter() - t0, raw)
                if not raw:
                    self.state_changed.emit("idle")
                    return
                if prep is not None:
                    prep.join(timeout=1.0)  # surrounding text is usually ready long before this
                self.state_changed.emit("cleaning")
                text, used_ai = self.cleaner.clean(raw, ctx)
                if not used_ai and self.settings.ai_cleanup:
                    self.message.emit("AI cleanup unavailable",
                                      f"{self.settings.provider} did not respond; basic cleanup was used.")
                hold = tuple(self.hotkey.keys) if self.hotkey else ()
                insert_text(text, self.settings.auto_paste, self.settings.clipboard_mode or not self.settings.auto_paste, hold)
                elapsed = time.perf_counter() - t0
                log.info("final (%.2fs, %s): %s", elapsed, ctx.category if ctx else "-", text)
                self.history.add(ctx.process if ctx else "", ctx.category if ctx else "", raw, text,
                                 self.settings.provider if used_ai else "basic", round(elapsed, 2))
                self.dictation_done.emit(text)
                self.state_changed.emit("idle")
            except Exception as e:
                log.exception("dictation failed")
                self.state_changed.emit("error")
                self.message.emit("Dictation failed", str(e))
