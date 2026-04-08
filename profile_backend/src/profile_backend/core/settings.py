"""Environment-driven runtime settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_path(key: str, default: Path) -> Path:
    raw = os.environ.get(key)
    if raw:
        return Path(raw).expanduser().resolve()
    return default


@dataclass(frozen=True)
class Settings:
    project_root: Path
    storage_root: Path
    inbox_dir: Path
    organized_root: Path
    spreadsheet_path: Path
    log_dir: Path
    spacy_model: str
    llm_provider: str
    llm_model: str
    openai_api_key: str
    openai_base_url: str
    deepai_api_key: str
    deepai_api_url: str
    textrazor_api_key: str
    textrazor_api_url: str
    ollama_api_url: str
    ollama_model: str
    google_creds_json: str
    google_process_creds_json: str
    google_upload_creds_json: str
    google_drive_creds_json: str
    google_sheets_creds_json: str
    gdrive_inbox_folder_id: str
    gdrive_root_folder_id: str
    gsheets_spreadsheet_id: str
    gsheets_sheet_name: str
    gdrive_share_with_emails: str
    profile_filename_template: str
    cors_origins: str


def load_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[4]
    storage_root = _env_path("PROFILE_STORAGE_ROOT", project_root / "data" / "storage")
    google_creds_json = os.environ.get("PROFILE_GOOGLE_CREDS_JSON", "")
    process_creds = os.environ.get(
        "PROFILE_GOOGLE_PROCESS_CREDS_JSON",
        str(project_root / "service-account.json"),
    )
    return Settings(
        project_root=project_root,
        storage_root=storage_root,
        inbox_dir=_env_path("PROFILE_INBOX_DIR", storage_root / "inbox"),
        organized_root=_env_path("PROFILE_ORGANIZED_ROOT", storage_root / "root"),
        spreadsheet_path=_env_path(
            "PROFILE_SPREADSHEET_PATH", project_root / "data" / "profiles.xlsx"
        ),
        log_dir=_env_path("PROFILE_LOG_DIR", project_root / "logs"),
        spacy_model=os.environ.get("PROFILE_SPACY_MODEL", "en_core_web_sm"),
        llm_provider=os.environ.get("PROFILE_LLM_PROVIDER", "ollama"),
        llm_model=os.environ.get("PROFILE_LLM_MODEL", "gpt-4o-mini"),
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        openai_base_url=os.environ.get("OPENAI_BASE_URL", ""),
        deepai_api_key=os.environ.get("DEEPAI_API_KEY", ""),
        deepai_api_url=os.environ.get(
            "DEEPAI_API_URL", "https://api.deepai.org/api/text-generator"
        ),
        textrazor_api_key=os.environ.get("TEXTRAZOR_API_KEY", ""),
        textrazor_api_url=os.environ.get("TEXTRAZOR_API_URL", "https://api.textrazor.com/"),
        ollama_api_url=os.environ.get("OLLAMA_API_URL", "http://127.0.0.1:11434/api/chat"),
        ollama_model=os.environ.get("OLLAMA_MODEL", "llama3.1:8b"),
        google_creds_json=google_creds_json,
        google_process_creds_json=process_creds,
        google_upload_creds_json=os.environ.get(
            "PROFILE_GOOGLE_UPLOAD_CREDS_JSON",
            str(project_root / "client-secret.json"),
        ),
        google_drive_creds_json=os.environ.get(
            "PROFILE_GOOGLE_DRIVE_CREDS_JSON", process_creds or google_creds_json
        ),
        google_sheets_creds_json=os.environ.get(
            "PROFILE_GOOGLE_SHEETS_CREDS_JSON", process_creds or google_creds_json
        ),
        gdrive_inbox_folder_id=os.environ.get("PROFILE_GDRIVE_INBOX_FOLDER_ID", ""),
        gdrive_root_folder_id=os.environ.get("PROFILE_GDRIVE_ROOT_FOLDER_ID", ""),
        gsheets_spreadsheet_id=os.environ.get("PROFILE_GSHEETS_SPREADSHEET_ID", ""),
        gsheets_sheet_name=os.environ.get("PROFILE_GSHEETS_SHEET_NAME", "Sheet1"),
        gdrive_share_with_emails=os.environ.get("PROFILE_GDRIVE_SHARE_WITH_EMAILS", ""),
        profile_filename_template="{first}_{last}_Profile",
        cors_origins=os.environ.get("PROFILE_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"),
    )


settings = load_settings()
