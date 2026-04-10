"""Persist registered Google cloud credential bundles under storage_root."""

from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path

from profile_backend.src.profile_backend.application.google_cloud_config import GoogleCloudRuntimeConfig
from profile_backend.src.profile_backend.core.settings import settings

_META = "meta.json"
_SERVICE_ACCOUNT = "service_account.json"
_CLIENT_SECRET = "client_secret.json"
_DRIVE = "drive_credentials.json"
_SHEETS = "sheets_credentials.json"

_SAFE_ID = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")


def _configs_root() -> Path:
    return (settings.storage_root / "google_cloud_configs").resolve()


def _parse_json_file(data: bytes, label: str) -> None:
    if not data:
        raise ValueError(f"{label}: empty file.")
    try:
        parsed = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label}: invalid JSON ({exc}).") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{label}: JSON must be an object.")


def register_google_cloud_config(
    *,
    service_account_bytes: bytes,
    client_secret_bytes: bytes | None,
    drive_credentials_bytes: bytes | None,
    sheets_credentials_bytes: bytes | None,
    gdrive_inbox_folder_id: str,
    gdrive_root_folder_id: str,
    gsheets_spreadsheet_id: str,
    gsheets_sheet_name: str | None,
    gdrive_share_with_emails: str | None,
) -> str:
    _parse_json_file(service_account_bytes, "service_account")
    if client_secret_bytes is not None:
        _parse_json_file(client_secret_bytes, "client_secret")
    if drive_credentials_bytes is not None:
        _parse_json_file(drive_credentials_bytes, "drive_credentials")
    if sheets_credentials_bytes is not None:
        _parse_json_file(sheets_credentials_bytes, "sheets_credentials")

    inbox = (gdrive_inbox_folder_id or "").strip()
    root = (gdrive_root_folder_id or "").strip()
    sheet_id = (gsheets_spreadsheet_id or "").strip()
    if not inbox or not root or not sheet_id:
        raise ValueError("gdrive_inbox_folder_id, gdrive_root_folder_id, and gsheets_spreadsheet_id are required.")

    config_id = str(uuid.uuid4())
    base = _configs_root() / config_id
    base.mkdir(parents=True, exist_ok=False)
    (base / _SERVICE_ACCOUNT).write_bytes(service_account_bytes)
    if client_secret_bytes is not None:
        (base / _CLIENT_SECRET).write_bytes(client_secret_bytes)
    if drive_credentials_bytes is not None:
        (base / _DRIVE).write_bytes(drive_credentials_bytes)
    if sheets_credentials_bytes is not None:
        (base / _SHEETS).write_bytes(sheets_credentials_bytes)

    meta = {
        "gdrive_inbox_folder_id": inbox,
        "gdrive_root_folder_id": root,
        "gsheets_spreadsheet_id": sheet_id,
        "gsheets_sheet_name": (gsheets_sheet_name or "").strip() or "Sheet1",
        "gdrive_share_with_emails": (gdrive_share_with_emails or "").strip(),
    }
    (base / _META).write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return config_id


def load_google_cloud_config(config_id: str) -> GoogleCloudRuntimeConfig:
    cid = (config_id or "").strip()
    if not _SAFE_ID.match(cid):
        raise ValueError("Invalid config_id.")
    base = (_configs_root() / cid).resolve()
    root = _configs_root().resolve()
    if not str(base).startswith(str(root)) or not base.is_dir():
        raise FileNotFoundError("Unknown config_id.")

    meta_path = base / _META
    if not meta_path.is_file():
        raise FileNotFoundError("Unknown config_id.")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    sa = base / _SERVICE_ACCOUNT
    if not sa.is_file():
        raise FileNotFoundError("Config bundle is incomplete.")

    drive_path = base / _DRIVE if (base / _DRIVE).is_file() else sa
    sheets_path = base / _SHEETS if (base / _SHEETS).is_file() else sa
    if (base / _CLIENT_SECRET).is_file():
        upload_path = base / _CLIENT_SECRET
    else:
        upload_path = sa

    return GoogleCloudRuntimeConfig(
        google_drive_creds_json=str(drive_path),
        google_sheets_creds_json=str(sheets_path),
        google_upload_creds_json=str(upload_path),
        gdrive_inbox_folder_id=str(meta.get("gdrive_inbox_folder_id", "")),
        gdrive_root_folder_id=str(meta.get("gdrive_root_folder_id", "")),
        gsheets_spreadsheet_id=str(meta.get("gsheets_spreadsheet_id", "")),
        gsheets_sheet_name=str(meta.get("gsheets_sheet_name", "Sheet1") or "Sheet1"),
        gdrive_share_with_emails=str(meta.get("gdrive_share_with_emails", "") or ""),
    )


def delete_google_cloud_config(config_id: str) -> bool:
    cid = (config_id or "").strip()
    if not _SAFE_ID.match(cid):
        return False
    base = (_configs_root() / cid).resolve()
    root = _configs_root().resolve()
    if not str(base).startswith(str(root)) or not base.is_dir():
        return False
    shutil.rmtree(base, ignore_errors=False)
    return True
