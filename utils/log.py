import logging
from logging.handlers import RotatingFileHandler

from utils.paths import data_dir


def setup_logging() -> None:
    handler = RotatingFileHandler(data_dir() / "voiceflow.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8")
    logging.basicConfig(level=logging.INFO, handlers=[handler, logging.StreamHandler()],
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
