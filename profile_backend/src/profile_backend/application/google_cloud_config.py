"""Runtime Google Drive/Sheets configuration (env defaults or per-request tenant bundle)."""

from __future__ import annotations

from dataclasses import dataclass

from profile_backend.src.profile_backend.core.settings import settings


@dataclass(frozen=True)
class GoogleCloudRuntimeConfig:
    """Paths to credential JSON files on disk plus Drive/Sheets folder IDs."""

    google_drive_creds_json: str
    google_sheets_creds_json: str
    google_upload_creds_json: str
    gdrive_inbox_folder_id: str
    gdrive_root_folder_id: str
    gsheets_spreadsheet_id: str
    gsheets_sheet_name: str
    gdrive_share_with_emails: str

    @staticmethod
    def from_settings() -> GoogleCloudRuntimeConfig:
        s = settings
        return GoogleCloudRuntimeConfig(
            google_drive_creds_json=s.google_drive_creds_json,
            google_sheets_creds_json=s.google_sheets_creds_json,
            google_upload_creds_json=s.google_upload_creds_json,
            gdrive_inbox_folder_id=s.gdrive_inbox_folder_id,
            gdrive_root_folder_id=s.gdrive_root_folder_id,
            gsheets_spreadsheet_id=s.gsheets_spreadsheet_id,
            gsheets_sheet_name=s.gsheets_sheet_name,
            gdrive_share_with_emails=s.gdrive_share_with_emails,
        )


def validate_cloud_config(cfg: GoogleCloudRuntimeConfig) -> None:
    missing: list[str] = []
    if not (cfg.google_drive_creds_json or "").strip():
        missing.append("Google Drive credentials path (drive)")
    if not (cfg.google_sheets_creds_json or "").strip():
        missing.append("Google Sheets credentials path (sheets)")
    if not (cfg.gdrive_inbox_folder_id or "").strip():
        missing.append("inbox folder id (PROFILE_GDRIVE_INBOX_FOLDER_ID)")
    if not (cfg.gdrive_root_folder_id or "").strip():
        missing.append("root folder id (PROFILE_GDRIVE_ROOT_FOLDER_ID)")
    if not (cfg.gsheets_spreadsheet_id or "").strip():
        missing.append("spreadsheet id (PROFILE_GSHEETS_SPREADSHEET_ID)")
    if missing:
        raise RuntimeError("Missing cloud config: " + ", ".join(missing))


def validate_upload_config(cfg: GoogleCloudRuntimeConfig) -> None:
    if not (cfg.google_upload_creds_json or "").strip():
        raise RuntimeError("Missing upload credentials path (PROFILE_GOOGLE_UPLOAD_CREDS_JSON or tenant upload file).")
    if not (cfg.gdrive_inbox_folder_id or "").strip():
        raise RuntimeError("Missing inbox folder id for upload.")
