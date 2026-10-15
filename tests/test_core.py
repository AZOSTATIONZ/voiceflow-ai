import json

import numpy as np
import pytest

from ai.cleanup import Cleaner, basic_cleanup, postprocess
from ai.prompts import build_system_prompt, build_user_prompt
from app.hotkey import HoldHotkey, normalize, parse_hotkey
from context.categories import categorize
from context.detector import AppContext
from db.history import History
from settings.settings import Settings, SettingsStore


@pytest.mark.parametrize("process,title,expected", [
    ("code.exe", "main.py - Visual Studio Code", "programming"),
    ("cursor.exe", "app.ts", "programming"),
    ("outlook.exe", "Inbox", "email"),
    ("slack.exe", "general", "chat"),
    ("winword.exe", "Report.docx", "document"),
    ("chrome.exe", "Inbox (3) - me@gmail.com - Gmail", "email"),
    ("msedge.exe", "Project plan - Google Docs", "document"),
    ("chrome.exe", "YouTube", "general"),
])
def test_categorize(process, title, expected):
    assert categorize(process, title) == expected


def test_hotkey_parsing():
    assert parse_hotkey("Ctrl+Win") == {"ctrl", "windows"}
    assert normalize("left windows") == "windows"
    with pytest.raises(ValueError):
        parse_hotkey("")


class _Ev:
    def __init__(self, name, kind):
        self.name, self.event_type = name, kind


def test_hold_hotkey_press_release(monkeypatch):
    monkeypatch.setattr("app.hotkey.win32api.keybd_event", lambda *a: None)
    calls = []
    hk = HoldHotkey("ctrl+windows", lambda: calls.append("down"), lambda: calls.append("up"))
    for name, kind in [("left ctrl", "down"), ("left windows", "down"), ("left windows", "down"),
                       ("left windows", "up"), ("left ctrl", "up")]:
        hk._handle(_Ev(name, kind))
    assert calls == ["down", "up"]


def test_basic_cleanup():
    assert basic_cleanup("um so i think uh we should ship it") == "So I think we should ship it."


def test_postprocess_strips_wrappers():
    assert postprocess('<think>hmm</think>"Hello, world."') == "Hello, world."
    assert postprocess("Here is the cleaned text:\n\nHi John,") == "Hi John,"


def test_prompts_include_context():
    ctx = AppContext(process="outlook.exe", title="New mail", category="email", text_before="Dear Sarah,")
    assert "email client" in build_system_prompt(ctx)
    user = build_user_prompt("thanks for the report", ctx)
    assert "Dear Sarah," in user and "<dictation>" in user


def test_cleaner_falls_back_when_provider_down():
    s = Settings(provider="ollama", ollama_host="http://127.0.0.1:9")
    text, used_ai = Cleaner(s).clean("hello there")
    assert text == "Hello there." and used_ai is False


def test_cleaner_uses_provider(monkeypatch):
    class Fake:
        def complete(self, system, user):
            return "Okay, update the API endpoint."
    monkeypatch.setattr("ai.cleanup.create_provider", lambda s: Fake())
    assert Cleaner(Settings()).clean("okay um update the api endpoint") == ("Okay, update the API endpoint.", True)


@pytest.mark.parametrize("raw,out,bad", [
    ("what is the capital city of symbabwe", "Zimbabwe", True),
    ("tell me a joke about cats", "I can't help with that.", True),
    ("how do i um reset my password on outlook", "reset my password on outlook", True),
    ("how do i um reset my password on outlook", "How do I reset my password on Outlook?", False),
    ("okay so um we need to ship it", "We need to ship it.", False),
    ("hey john thanks for coming", "Hi John,\n\nThanks for coming.\n\nBest regards,", False),
])
def test_looks_wrong(raw, out, bad):
    from ai.cleanup import looks_wrong
    assert looks_wrong(raw, out) is bad


def test_ollama_avoids_localhost_ipv6_delay():
    from ai.providers import OllamaProvider
    assert OllamaProvider("llama3.2", host="http://localhost:11434/").host == "http://127.0.0.1:11434"


def test_history_roundtrip_and_export(tmp_path):
    h = History(tmp_path / "h.db")
    h.add("code.exe", "programming", "raw", "Final text.", "ollama", 1.2)
    h.add("slack.exe", "chat", "raw2", "hey team", "ollama", 0.8)
    assert len(h.search()) == 2
    assert [r["app"] for r in h.search("team")] == ["slack.exe"]
    for ext in ("txt", "csv", "json"):
        h.export(str(tmp_path / f"out.{ext}"))
    assert len(json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))) == 2


def test_settings_persist(tmp_path):
    store = SettingsStore(tmp_path / "s.json")
    store.settings.whisper_model = "small"
    store.settings.models["ollama"] = "gemma2"
    store.save()
    again = SettingsStore(tmp_path / "s.json").settings
    assert again.whisper_model == "small" and again.model_for("ollama") == "gemma2"
    assert again.model_for("anthropic")  # defaults merged in


def test_transcriber_empty_audio():
    from audio.transcriber import Transcriber
    assert Transcriber("tiny").transcribe(np.zeros(0, dtype=np.float32)) == ""
