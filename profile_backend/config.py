"""Paths and tunables (local storage)."""

from __future__ import annotations

import os
from pathlib import Path

# Project root: parent of profile_backend package
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _env_path(key: str, default: Path) -> Path:
    raw = os.environ.get(key)
    if raw:
        return Path(raw).expanduser().resolve()
    return default


STORAGE_ROOT = _env_path("PROFILE_STORAGE_ROOT", _PROJECT_ROOT / "data" / "storage")
INBOX_DIR = _env_path("PROFILE_INBOX_DIR", STORAGE_ROOT / "inbox")
ORGANIZED_ROOT = _env_path("PROFILE_ORGANIZED_ROOT", STORAGE_ROOT / "root")
SPREADSHEET_PATH = _env_path(
    "PROFILE_SPREADSHEET_PATH", _PROJECT_ROOT / "data" / "profiles.xlsx"
)
LOG_DIR = _env_path("PROFILE_LOG_DIR", _PROJECT_ROOT / "logs")

SPACY_MODEL = os.environ.get("PROFILE_SPACY_MODEL", "en_core_web_sm")

# Filename for organized files (without extension handling elsewhere)
PROFILE_FILENAME_TEMPLATE = "{first}_{last}_Profile"
