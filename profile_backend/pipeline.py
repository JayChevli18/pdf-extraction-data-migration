"""End-to-end processing: inbox -> organize -> sheet."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from profile_backend.config import (
    INBOX_DIR,
    ORGANIZED_ROOT,
    PROFILE_FILENAME_TEMPLATE,
    SPREADSHEET_PATH,
)
from profile_backend.ai_extractor import AIExtractedFields, extract_fields_ai_provider
from profile_backend.ids import generate_profile_id
from profile_backend.models import ProfileRecord
from profile_backend.organize import (
    file_share_link,
    filename_from_name,
    gender_folder,
    move_to_organized,
    year_folder_from_dob,
)
from profile_backend.spreadsheet import append_record
from profile_backend.text_extract import extract_text

logger = logging.getLogger("profile_backend.pipeline")

_SUPPORTED = {".pdf", ".docx"}


def list_inbox_files() -> list[Path]:
    if not INBOX_DIR.is_dir():
        INBOX_DIR.mkdir(parents=True, exist_ok=True)
        return []
    files = [
        p
        for p in INBOX_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in _SUPPORTED
    ]
    return sorted(files, key=lambda x: x.name.lower())


def _build_record(
    extracted: AIExtractedFields,
    dob_for_year: str | None,
    final_path: Path,
    upload_date: str,
) -> ProfileRecord:
    pid = generate_profile_id(extracted.dob or dob_for_year)
    year_val = ""
    if extracted.dob and len(extracted.dob) >= 4:
        year_val = extracted.dob[:4]
    elif dob_for_year and len(dob_for_year) >= 4:
        year_val = dob_for_year[:4]

    return ProfileRecord(
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
        drive_link=file_share_link(final_path),
        upload_date=upload_date,
        year=year_val,
    )


def process_one(path: Path) -> ProfileRecord:
    """Process a single PDF/DOCX from inbox (caller must ensure path is in inbox)."""
    logger.info("Processing file: %s", path)
    text = extract_text(path)
    if not text.strip():
        logger.warning("No text extracted from %s", path)

    # AI-only extraction for multilingual/unstructured documents
    extracted = extract_fields_ai_provider(text)
    logger.debug("AI extraction: name=%s dob=%s gender=%s", extracted.name, extracted.dob, extracted.gender)

    # Steps 3–4 — organize + rename using AI extracted values
    year_dir = year_folder_from_dob(extracted.dob)
    gender_dir = gender_folder(extracted.gender)
    base_name = filename_from_name(extracted.name, PROFILE_FILENAME_TEMPLATE)
    upload_date = date.today().isoformat()

    final_path = move_to_organized(
        path,
        ORGANIZED_ROOT,
        year=year_dir,
        gender=gender_dir,
        new_base_name=base_name,
    )

    dob_for_row = extracted.dob
    record = _build_record(
        extracted,
        dob_for_year=dob_for_row,
        final_path=final_path,
        upload_date=upload_date,
    )
    append_record(SPREADSHEET_PATH, record)
    logger.info("Finished processing: %s -> id=%s", final_path, record.id)
    return record


def process_inbox() -> list[ProfileRecord]:
    """Process all supported files in the inbox in sorted order."""
    results: list[ProfileRecord] = []
    for path in list_inbox_files():
        try:
            results.append(process_one(path))
        except Exception as e:
            logger.exception("Failed processing %s: %s", path, e)
    return results
