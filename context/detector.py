import logging
from dataclasses import dataclass

import psutil
import win32gui
import win32process

from context.categories import categorize

log = logging.getLogger(__name__)
CONTEXT_CHARS = 500


@dataclass
class AppContext:
    hwnd: int = 0
    process: str = ""
    title: str = ""
    category: str = "general"
    text_before: str = ""
    text_after: str = ""


def _surrounding_text() -> tuple[str, str]:
    """Best-effort read of text around the caret via UI Automation. Many apps don't expose it."""
    try:
        import uiautomation as auto
        with auto.UIAutomationInitializerInThread():  # called from worker threads
            return _read_caret_text(auto)
    except Exception as e:
        log.debug("surrounding text unavailable: %s", e)
    return "", ""


def _read_caret_text(auto) -> tuple[str, str]:
    try:
        ctrl = auto.GetFocusedControl()
        if ctrl is None:
            return "", ""
        pattern = ctrl.GetPattern(auto.PatternId.TextPattern)
        if pattern:
            selections = pattern.GetSelection()
            if selections:
                caret = selections[0]
                doc = pattern.DocumentRange
                before = doc.Clone()
                before.MoveEndpointByRange(auto.TextPatternRangeEndpoint.End, caret, auto.TextPatternRangeEndpoint.Start)
                after = doc.Clone()
                after.MoveEndpointByRange(auto.TextPatternRangeEndpoint.Start, caret, auto.TextPatternRangeEndpoint.End)
                return before.GetText(-1)[-CONTEXT_CHARS:], after.GetText(-1)[:CONTEXT_CHARS]
        value = ctrl.GetPattern(auto.PatternId.ValuePattern)
        if value and value.Value:
            return value.Value[-CONTEXT_CHARS:], ""
    except Exception as e:
        log.debug("surrounding text unavailable: %s", e)
    return "", ""


def detect_context(read_text: bool = True) -> AppContext:
    ctx = AppContext()
    try:
        ctx.hwnd = win32gui.GetForegroundWindow()
        ctx.title = win32gui.GetWindowText(ctx.hwnd)
        _, pid = win32process.GetWindowThreadProcessId(ctx.hwnd)
        ctx.process = psutil.Process(pid).name().lower()
    except Exception as e:
        log.debug("foreground detection failed: %s", e)
    ctx.category = categorize(ctx.process, ctx.title)
    if read_text:
        ctx.text_before, ctx.text_after = _surrounding_text()
    return ctx
