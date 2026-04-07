"""Light parse: DOB and gender hints before full extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from profile_backend.nlp_utils import get_nlp


@dataclass
class LightMetadata:
    date_of_birth: str | None  # ISO YYYY-MM-DD when parsed
    gender: str | None  # Male / Female / Other


_DATE_PATTERNS = [
    re.compile(
        r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b"
    ),  # DD/MM/YYYY or MM/DD/YYYY — heuristic below
    re.compile(
        r"\b(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})\b"
    ),  # YYYY-MM-DD
]


def _try_parse_date(s: str) -> datetime | None:
    s = s.strip()
    for pat in _DATE_PATTERNS:
        m = pat.search(s)
        if not m:
            continue
        g = m.groups()
        try:
            if len(g[0]) == 4:  # year first
                y, mo, d = int(g[0]), int(g[1]), int(g[2])
            else:
                # Assume DD/MM/YYYY (common outside US for profiles)
                d, mo, y = int(g[0]), int(g[1]), int(g[2])
                if y < 100:
                    y += 1900 if y > 30 else 2000
            return datetime(y, mo, d)
        except (ValueError, OverflowError):
            continue
    return None


_GENDER_WORDS = {
    "male": "Male",
    "female": "Female",
    "m": "Male",
    "f": "Female",
}


def extract_light_metadata(text: str) -> LightMetadata:
    """Best-effort DOB and gender from raw text (no guessing beyond patterns)."""
    text_lower = text.lower()
    dob: str | None = None

    nlp = get_nlp()
    doc = nlp(text[:100_000])  # cap for speed
    for ent in doc.ents:
        if ent.label_ == "DATE":
            dt = _try_parse_date(ent.text)
            if dt and 1920 <= dt.year <= datetime.now().year:
                dob = dt.strftime("%Y-%m-%d")
                break

    if dob is None:
        for line in text.splitlines():
            for pat in _DATE_PATTERNS:
                m = pat.search(line)
                if m:
                    dt = _try_parse_date(m.group(0))
                    if dt and 1920 <= dt.year <= datetime.now().year:
                        dob = dt.strftime("%Y-%m-%d")
                        break
            if dob:
                break

    gender: str | None = None
    for w, label in _GENDER_WORDS.items():
        if re.search(rf"\b{re.escape(w)}\b", text_lower):
            gender = label
            break

    return LightMetadata(date_of_birth=dob, gender=gender)
