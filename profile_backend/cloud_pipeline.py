"""Cloud pipeline: Google Drive inbox -> organize in Drive -> append to Google Sheets."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from profile_backend.ai_extractor import extract_fields_ai_provider
from profile_backend.config import (
    GOOGLE_CREDS_JSON,
    GDRIVE_INBOX_FOLDER_ID,
    GDRIVE_ROOT_FOLDER_ID,
    GSHEETS_SHEET_NAME,
    GSHEETS_SPREADSHEET_ID,
    PROFILE_FILENAME_TEMPLATE,
)
from profile_backend.gdrive_client import (
    build_drive_service,
    download_file_bytes,
    ensure_folder,
    ensure_share_link,
    list_inbox_files,
    move_and_rename_file,
)
from profile_backend.gsheets_client import build_sheets_service, append_row
from profile_backend.ids import generate_profile_id
from profile_backend.models import ProfileRecord
from profile_backend.organize import (
    filename_from_name,
    gender_folder,
    year_folder_from_dob,
)
from profile_backend.text_extract import extract_text_bytes

logger = logging.getLogger("profile_backend.cloud_pipeline")


def _suffix_from_mime(mime_type: str, name: str) -> str:
    mt = (mime_type or "").lower()
    if mt == "application/pdf":
        return ".pdf"
    if mt == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return ".docx"
    # fallback to filename extension
    return Path(name).suffix.lower()


def process_cloud_inbox() -> list[ProfileRecord]:
    _validate_cloud_config()
    drive = build_drive_service(GOOGLE_CREDS_JSON)
    sheets = build_sheets_service(GOOGLE_CREDS_JSON)

    results: list[ProfileRecord] = []
    for f in list_inbox_files(drive, GDRIVE_INBOX_FOLDER_ID):
        try:
            results.append(process_cloud_one(drive, sheets, f.id, f.name, f.mime_type))
        except Exception as e:
            logger.exception("Failed processing Drive file %s (%s): %s", f.name, f.id, e)
    return results


def process_cloud_one(drive, sheets, file_id: str, name: str, mime_type: str) -> ProfileRecord:
    _validate_cloud_config()

    logger.info("Processing Drive file: %s (%s)", name, file_id)
    data = download_file_bytes(drive, file_id)
    suffix = _suffix_from_mime(mime_type, name)
    text = extract_text_bytes(suffix, data)

    extracted = extract_fields_ai_provider(text)
    upload_date = date.today().isoformat()

    year_dir = year_folder_from_dob(extracted.dob)
    gender_dir = gender_folder(extracted.gender)
    base_name = filename_from_name(extracted.name, PROFILE_FILENAME_TEMPLATE)

    # Create Root/Year/Gender folders in Drive
    year_folder_id = ensure_folder(drive, GDRIVE_ROOT_FOLDER_ID, year_dir)
    gender_folder_id = ensure_folder(drive, year_folder_id, gender_dir)

    # Rename and move inside Drive
    new_name = f"{base_name}{suffix}"
    move_and_rename_file(drive, file_id=file_id, new_parent_id=gender_folder_id, new_name=new_name)

    # Share link
    share_link = ensure_share_link(drive, file_id)

    # System fields
    pid = generate_profile_id(extracted.dob)
    year_val = extracted.dob[:4] if extracted.dob and len(extracted.dob) >= 4 else ""

    record = ProfileRecord(
        id=pid,
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
        spreadsheet_id=GSHEETS_SPREADSHEET_ID,
        sheet_name=GSHEETS_SHEET_NAME,
        row_values=record.to_row_list(),
    )
    logger.info("Appended to Google Sheet: id=%s", record.id)
    return record


def _validate_cloud_config() -> None:
    missing = []
    if not GOOGLE_CREDS_JSON:
        missing.append("PROFILE_GOOGLE_CREDS_JSON")
    if not GDRIVE_INBOX_FOLDER_ID:
        missing.append("PROFILE_GDRIVE_INBOX_FOLDER_ID")
    if not GDRIVE_ROOT_FOLDER_ID:
        missing.append("PROFILE_GDRIVE_ROOT_FOLDER_ID")
    if not GSHEETS_SPREADSHEET_ID:
        missing.append("PROFILE_GSHEETS_SPREADSHEET_ID")
    if missing:
        raise RuntimeError("Missing cloud config env vars: " + ", ".join(missing))

