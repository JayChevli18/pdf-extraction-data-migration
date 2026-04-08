"""Rules for foldering and naming organized files."""

from __future__ import annotations

import logging
import re
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("profile_backend.domain.organize")


def _safe_segment(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*]', "_", value.strip())
    return value or "Unknown"


def year_folder_from_dob(dob_iso: str | None) -> str:
    dob_normalized = normalize_dob(dob_iso)
    if not dob_normalized:
        return "Unknown"
    return dob_normalized[:4]


def normalize_dob(dob_raw: str | None) -> str:
    """
    Normalize DOB into ISO format YYYY-MM-DD.

    Supports common inputs like:
    - YYYY-MM-DD
    - DD-MM-YYYY
    - DD/MM/YYYY
    - DD.MM.YYYY
    """
    if not dob_raw:
        return ""
    value = dob_raw.strip()
    if not value:
        return ""

    formats = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y")
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    match = re.match(r"^\s*(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\s*$", value)
    if match:
        day, month, year = match.groups()
        try:
            return datetime(int(year), int(month), int(day)).strftime("%Y-%m-%d")
        except ValueError:
            return ""
    return ""


def gender_folder(gender: str | None) -> str:
    if not gender:
        return "Unknown"
    normalized = gender.strip().lower()
    if normalized in ("male", "m"):
        return "Male"
    if normalized in ("female", "f"):
        return "Female"
    return _safe_segment(gender)


def filename_from_name(full_name: str, template: str) -> str:
    name = full_name.strip()
    if not name:
        return template.format(first="Unknown", last="Unknown")
    parts = name.split()
    first = parts[0]
    last = parts[-1] if len(parts) > 1 else parts[0]
    return template.format(first=first.replace(" ", "_"), last=last.replace(" ", "_"))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def move_to_organized(
    src: Path,
    organized_root: Path,
    year: str,
    gender: str,
    new_base_name: str,
) -> Path:
    dest_dir = organized_root / _safe_segment(year) / _safe_segment(gender)
    ensure_dir(dest_dir)
    dest = dest_dir / f"{new_base_name}{src.suffix.lower()}"
    if dest.resolve() == src.resolve():
        return dest
    if dest.exists():
        idx = 1
        while True:
            candidate = dest_dir / f"{new_base_name}_{idx}{src.suffix.lower()}"
            if not candidate.exists():
                dest = candidate
                break
            idx += 1
    shutil.move(str(src), str(dest))
    logger.info("Moved %s -> %s", src, dest)
    return dest


def file_share_link(path: Path) -> str:
    return path.resolve().as_uri()
