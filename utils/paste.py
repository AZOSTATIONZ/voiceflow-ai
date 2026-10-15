import logging
import time

import keyboard
import pyperclip

log = logging.getLogger(__name__)


def insert_text(text: str, auto_paste: bool, keep_in_clipboard: bool, wait_release: tuple[str, ...] = ()) -> None:
    """Put text into the active app. Clipboard is restored afterwards unless keep_in_clipboard."""
    previous = None
    if not keep_in_clipboard:
        try:
            previous = pyperclip.paste()
        except Exception:
            previous = None
    pyperclip.copy(text)
    if not auto_paste:
        return
    deadline = time.time() + 1.5
    while time.time() < deadline and any(keyboard.is_pressed(k) for k in wait_release):
        time.sleep(0.02)
    keyboard.send("ctrl+v")
    if previous is not None:
        time.sleep(0.25)
        try:
            pyperclip.copy(previous)
        except Exception:
            log.warning("could not restore clipboard")
