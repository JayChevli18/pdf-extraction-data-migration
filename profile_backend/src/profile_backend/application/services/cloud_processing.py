"""Use-cases for cloud Drive->Sheet processing."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from profile_backend.src.profile_backend.core.settings import settings
from profile_backend.src.profile_backend.domain.ids import generate_profile_id
from profile_backend.src.profile_backend.domain.models import ProfileRecord
from profile_backend.src.profile_backend.domain.organize import (
    filename_from_name,
    gender_folder,
    normalize_dob,
    year_folder_from_dob,
)
from profile_backend.src.profile_backend.infrastructure.ai.extractor import extract_fields_ai_provider
from profile_backend.src.profile_backend.infrastructure.files.text_extract import extract_text_bytes
from profile_backend.src.profile_backend.infrastructure.google.drive_client import (
    build_drive_service,
    download_file_bytes,
    ensure_folder,
    ensure_share_link,
    list_inbox_files,
    move_and_rename_file,
    upload_file_to_folder,
)
from profile_backend.src.profile_backend.infrastructure.google.sheets_client import (
    append_row,
    build_sheets_service,
)

logger = logging.getLogger("profile_backend.application.cloud_processing")


def _suffix_from_mime(mime_type: str, name: str) -> str:
    mt = (mime_type or "").lower()
    if mt == "application/pdf":
        return ".pdf"
    if mt == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return ".docx"
    return Path(name).suffix.lower()


def _validate_cloud_config() -> None:
    missing = []
    if not settings.google_drive_creds_json:
        missing.append("PROFILE_GOOGLE_DRIVE_CREDS_JSON or PROFILE_GOOGLE_CREDS_JSON")
    if not settings.google_sheets_creds_json:
        missing.append("PROFILE_GOOGLE_SHEETS_CREDS_JSON or PROFILE_GOOGLE_CREDS_JSON")
    if not settings.gdrive_inbox_folder_id:
        missing.append("PROFILE_GDRIVE_INBOX_FOLDER_ID")
    if not settings.gdrive_root_folder_id:
        missing.append("PROFILE_GDRIVE_ROOT_FOLDER_ID")
    if not settings.gsheets_spreadsheet_id:
        missing.append("PROFILE_GSHEETS_SPREADSHEET_ID")
    if missing:
        raise RuntimeError("Missing cloud config env vars: " + ", ".join(missing))


def process_cloud_inbox() -> list[ProfileRecord]:
    _validate_cloud_config()
    drive = build_drive_service(settings.google_drive_creds_json)
    sheets = build_sheets_service(settings.google_sheets_creds_json)
    results: list[ProfileRecord] = []
    for f in list_inbox_files(drive, settings.gdrive_inbox_folder_id):
        try:
            results.append(process_cloud_one(drive, sheets, f.id, f.name, f.mime_type))
        except Exception as exc:
            logger.exception("Failed processing Drive file %s (%s): %s", f.name, f.id, exc)
    return results


def process_cloud_one(drive, sheets, file_id: str, name: str, mime_type: str) -> ProfileRecord:
    _validate_cloud_config()
    data = download_file_bytes(drive, file_id)
    suffix = _suffix_from_mime(mime_type, name)
    text = extract_text_bytes(suffix, data)
    extracted = extract_fields_ai_provider(text)
    extracted.dob = normalize_dob(extracted.dob) or extracted.dob

    year_dir = year_folder_from_dob(extracted.dob)
    gender_dir = gender_folder(extracted.gender)
    base_name = filename_from_name(extracted.name, settings.profile_filename_template)

    year_folder_id = ensure_folder(drive, settings.gdrive_root_folder_id, year_dir)
    gender_folder_id = ensure_folder(drive, year_folder_id, gender_dir)
    move_and_rename_file(drive, file_id=file_id, new_parent_id=gender_folder_id, new_name=f"{base_name}{suffix}")

    share_emails = [e.strip() for e in settings.gdrive_share_with_emails.split(",") if e.strip()]
    share_link = ensure_share_link(drive, file_id, share_with_emails=share_emails)
    upload_date = date.today().isoformat()
    year_val = year_folder_from_dob(extracted.dob)
    if year_val == "Unknown":
        year_val = ""

    record = ProfileRecord(
        id=generate_profile_id(extracted.dob),
        name=extracted.name,
        gender=extracted.gender,
        dob=extracted.dob,
        birth_place=extracted.birth_place,
        birth_time=extracted.birth_time,
        height=extracted.height,
        religion_caste=extracted.religion_caste,
        contact_number=extracted.contact_number,
        email=extracted.email,
        address=extracted.address,
        occupation_work=extracted.occupation_work,
        salary=extracted.salary,
        education=extracted.education,
        father_name=extracted.father_name,
        father_occupation=extracted.father_occupation,
        mother_name=extracted.mother_name,
        mother_occupation=extracted.mother_occupation,
        hobbies=extracted.hobbies,
        preferences=extracted.preferences,
        diet_preference=extracted.diet_preference,
        brothers=extracted.brothers,
        sisters=extracted.sisters,
        drive_link=share_link,
        upload_date=upload_date,
        year=year_val,
    )
    append_row(
        sheets,
        spreadsheet_id=settings.gsheets_spreadsheet_id,
        sheet_name=settings.gsheets_sheet_name,
        row_values=record.to_row_list(),
    )
    return record


def upload_to_cloud_inbox(uploaded_files) -> list[dict[str, str]]:
    drive = build_drive_service(settings.google_upload_creds_json)
    allowed = {".pdf", ".docx"}
    results: list[dict[str, str]] = []
    for f in uploaded_files:
        name = (f.filename or "").strip()
        if not name:
            raise ValueError("One file is missing a filename.")
        if not any(name.lower().endswith(ext) for ext in allowed):
            raise ValueError(f"Unsupported file type for '{name}'. Only PDF/DOCX.")
        data = f.read()
        uploaded = upload_file_to_folder(
            drive,
            parent_folder_id=settings.gdrive_inbox_folder_id,
            file_name=name,
            data=data,
            mime_type=f.mimetype or None,
        )
        results.append({"id": uploaded.id, "name": uploaded.name, "mimeType": uploaded.mime_type})
    return results
