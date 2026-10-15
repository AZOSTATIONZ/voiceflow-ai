import json
import logging
from dataclasses import asdict, dataclass, field, fields

from utils.paths import data_dir

log = logging.getLogger(__name__)

PROVIDERS = ["ollama", "anthropic", "openai", "gemini", "mistral", "deepseek"]
DEFAULT_MODELS = {
    "ollama": "llama3.2",
    "anthropic": "claude-haiku-5-5",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
    "mistral": "mistral-small-latest",
    "deepseek": "deepseek-chat",
}
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v3"]
LANGUAGES = {"Auto-detect": "auto", "English": "en", "Spanish": "es", "French": "fr", "German": "de",
             "Portuguese": "pt", "Italian": "it", "Dutch": "nl", "Hindi": "hi", "Japanese": "ja",
             "Chinese": "zh", "Arabic": "ar", "Russian": "ru"}


@dataclass
class Settings:
    hotkey: str = "ctrl+windows"
    whisper_model: str = "base"
    language: str = "en"  # auto-detect misfires on short clips (e.g. English heard as Japanese)
    mic_device: int | None = None
    provider: str = "ollama"
    models: dict = field(default_factory=lambda: dict(DEFAULT_MODELS))
    api_keys: dict = field(default_factory=dict)
    ollama_host: str = "http://127.0.0.1:11434"
    ai_cleanup: bool = True
    use_context: bool = True
    clipboard_mode: bool = False   # keep result in clipboard after pasting
    auto_paste: bool = True
    start_on_boot: bool = False
    update_url: str = ""           # optional JSON endpoint: {"version": "...", "url": "..."}

    def model_for(self, provider: str) -> str:
        return self.models.get(provider) or DEFAULT_MODELS[provider]


class SettingsStore:
    def __init__(self, path=None):
        self.path = path or data_dir() / "settings.json"
        self.settings = self.load()

    def load(self) -> Settings:
        s = Settings()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8-sig"))  # tolerate BOM from hand edits
            names = {f.name for f in fields(Settings)}
            for k, v in raw.items():
                if k in names:
                    setattr(s, k, v)
            s.models = {**DEFAULT_MODELS, **s.models}
        except FileNotFoundError:
            pass
        except Exception:
            log.exception("settings unreadable, using defaults")
        return s

    def save(self) -> None:
        self.path.write_text(json.dumps(asdict(self.settings), indent=2), encoding="utf-8")
