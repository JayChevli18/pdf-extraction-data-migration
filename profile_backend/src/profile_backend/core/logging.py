"""Application logging setup."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from profile_backend.src.profile_backend.core.settings import settings


def setup_logging(name: str = "profile_backend") -> logging.Logger:
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    log_path = settings.log_dir / "profile_backend.log"

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
