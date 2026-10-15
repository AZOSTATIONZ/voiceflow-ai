"""VoiceFlow AI entry point."""
import os
import sys

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from app.main import run  # noqa: E402

if __name__ == "__main__":
    sys.exit(run())
