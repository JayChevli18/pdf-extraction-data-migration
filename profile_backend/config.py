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
LLM_PROVIDER = os.environ.get("PROFILE_LLM_PROVIDER", "ollama")
LLM_MODEL = os.environ.get("PROFILE_LLM_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "")
DEEPAI_API_KEY = os.environ.get("DEEPAI_API_KEY", "")
DEEPAI_API_URL = os.environ.get(
    "DEEPAI_API_URL", "https://api.deepai.org/api/text-generator"
)
TEXTRAZOR_API_KEY = os.environ.get("TEXTRAZOR_API_KEY", "")
TEXTRAZOR_API_URL = os.environ.get("TEXTRAZOR_API_URL", "https://api.textrazor.com/")
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://127.0.0.1:11434/api/chat")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

# Filename for organized files (without extension handling elsewhere)
PROFILE_FILENAME_TEMPLATE = "{first}_{last}_Profile"
