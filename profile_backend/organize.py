"""Move/rename files under local Root / Year / Gender."""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path

logger = logging.getLogger("profile_backend.organize")


def _safe_segment(s: str) -> str:
    s = re.sub(r'[<>:"/\\|?*]', "_", s.strip())
    return s or "Unknown"


def year_folder_from_dob(dob_iso: str | None) -> str:
    """YYYY from ISO date, or 'Unknown'."""
    if not dob_iso or len(dob_iso) < 4:
        return "Unknown"
    try:
        y = int(dob_iso[:4])
        if 1900 <= y <= 2100:
            return str(y)
    except ValueError:
        pass
    return "Unknown"


def gender_folder(gender: str | None) -> str:
    if not gender:
        return "Unknown"
    g = gender.strip().lower()
    if g in ("male", "m"):
        return "Male"
    if g in ("female", "f"):
        return "Female"
    return _safe_segment(gender)


def filename_from_name(full_name: str, template: str) -> str:
    """Build FirstName_LastName_Profile; unknown parts as Unknown."""
    name = full_name.strip()
    if not name:
        return template.format(first="Unknown", last="Unknown")
    parts = name.split()
    if len(parts) == 1:
        first, last = parts[0], parts[0]
    else:
        first, last = parts[0], parts[-1]
    first = first.replace(" ", "_")
    last = last.replace(" ", "_")
    return template.format(first=first, last=last)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def move_to_organized(
    src: Path,
    organized_root: Path,
    year: str,
    gender: str,
    new_base_name: str,
) -> Path:
    """
    Move file to organized_root/year/gender/new_base_name + original suffix.
    Returns final path.
    """
    dest_dir = organized_root / _safe_segment(year) / _safe_segment(gender)
    ensure_dir(dest_dir)
    dest = dest_dir / f"{new_base_name}{src.suffix.lower()}"
    if dest.resolve() == src.resolve():
        return dest
    if dest.exists():
        logger.warning("Destination exists, adding suffix: %s", dest)
        n = 1
        while True:
            cand = dest_dir / f"{new_base_name}_{n}{src.suffix.lower()}"
            if not cand.exists():
                dest = cand
                break
            n += 1
    shutil.move(str(src), str(dest))
    logger.info("Moved %s -> %s", src, dest)
    return dest


def file_share_link(path: Path) -> str:
    """Read-only local URI for reference (replace with cloud link later)."""
    return path.resolve().as_uri()
