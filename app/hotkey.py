"""Global hold-to-talk hotkey built on a low-level keyboard hook."""
import logging
import threading

import keyboard
import win32api

log = logging.getLogger(__name__)
VK_UNASSIGNED = 0xFF  # tapping an unassigned key stops Windows opening Start when Win is released


def normalize(name: str) -> str:
    name = (name or "").lower().replace("left ", "").replace("right ", "")
    return {"win": "windows", "control": "ctrl", "option": "alt", "return": "enter"}.get(name, name)


def parse_hotkey(hotkey: str) -> frozenset[str]:
    keys = frozenset(normalize(k.strip()) for k in hotkey.split("+") if k.strip())
    if not keys:
        raise ValueError("empty hotkey")
    return keys


class HoldHotkey:
    def __init__(self, hotkey: str, on_press, on_release):
        self.keys = parse_hotkey(hotkey)
        self.on_press, self.on_release = on_press, on_release
        self._down: set[str] = set()
        self._active = False
        self._hook = None
        self._lock = threading.Lock()

    def start(self) -> None:
        self._hook = keyboard.hook(self._handle)
        log.info("hotkey registered: %s", "+".join(sorted(self.keys)))

    def stop(self) -> None:
        if self._hook:
            keyboard.unhook(self._hook)
            self._hook = None

    def _handle(self, event) -> None:
        name = normalize(event.name)
        if not name or name == "unknown":
            return
        fire = None
        with self._lock:
            if event.event_type == keyboard.KEY_DOWN:
                self._down.add(name)
                if not self._active and self.keys <= self._down:
                    self._active, fire = True, self.on_press
            else:
                self._down.discard(name)
                if self._active and name in self.keys:
                    self._active, fire = False, self.on_release
        if fire is self.on_press and "windows" in self.keys:
            win32api.keybd_event(VK_UNASSIGNED, 0, 0, 0)
            win32api.keybd_event(VK_UNASSIGNED, 0, 2, 0)
        if fire:
            try:
                fire()
            except Exception:
                log.exception("hotkey callback failed")
