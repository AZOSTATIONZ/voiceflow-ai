import os
import sys
from pathlib import Path

APP_NAME = "VoiceFlowAI"
VERSION = "1.0.0"


def data_dir() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def resource_path(rel: str) -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return root / rel
