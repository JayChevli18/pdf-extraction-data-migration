"""Use-cases for local inbox processing."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from profile_backend.src.profile_backend.core.settings import settings
from profile_backend.src.profile_backend.domain.ids import generate_profile_id
from profile_backend.src.profile_backend.domain.models import ProfileRecord
from profile_backend.src.profile_backend.domain.organize import (
    file_share_link,
    filename_from_name,
    gender_folder,
    move_to_organized,
    normalize_dob,
    year_folder_from_dob,
)
from profile_backend.src.profile_backend.infrastructure.ai.extractor import (
    AIExtractedFields,
    extract_fields_ai_provider,
)
from profile_backend.src.profile_backend.infrastructure.files.text_extract import extract_text
from profile_backend.src.profile_backend.infrastructure.storage.spreadsheet import append_record

logger = logging.getLogger("profile_backend.application.local_processing")

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def list_inbox_files() -> list[Path]:
    if not settings.inbox_dir.is_dir():
        settings.inbox_dir.mkdir(parents=True, exist_ok=True)
        return []
    files = [p for p in settings.inbox_dir.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
    return sorted(files, key=lambda x: x.name.lower())


def _build_record(
    extracted: AIExtractedFields,
    dob_for_year: str | None,
    final_path: Path,
    upload_date: str,
) -> ProfileRecord:
    normalized_dob = normalize_dob(extracted.dob) or extracted.dob
    pid = generate_profile_id(normalized_dob or dob_for_year)
    year_val = year_folder_from_dob(normalized_dob or dob_for_year)
    if year_val == "Unknown":
        year_val = ""

    return ProfileRecord(
        id=pid,
        name=extracted.name,
        gender=extracted.gender,
        dob=normalized_dob,
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
        drive_link=file_share_link(final_path),
        upload_date=upload_date,
        year=year_val,
    )


def process_one(path: Path) -> ProfileRecord:
    logger.info("Processing file: %s", path)
    text = extract_text(path)
    extracted = extract_fields_ai_provider(text)
    extracted.dob = normalize_dob(extracted.dob) or extracted.dob

    year_dir = year_folder_from_dob(extracted.dob)
    gender_dir = gender_folder(extracted.gender)
    base_name = filename_from_name(extracted.name, settings.profile_filename_template)
    upload_date = date.today().isoformat()

    final_path = move_to_organized(
        path,
        settings.organized_root,
        year=year_dir,
        gender=gender_dir,
        new_base_name=base_name,
    )
    record = _build_record(extracted, dob_for_year=extracted.dob, final_path=final_path, upload_date=upload_date)
    append_record(settings.spreadsheet_path, record)
    return record


def process_inbox() -> list[ProfileRecord]:
    results: list[ProfileRecord] = []
    for path in list_inbox_files():
        try:
            results.append(process_one(path))
        except Exception as exc:
            logger.exception("Failed processing %s: %s", path, exc)
    return results
