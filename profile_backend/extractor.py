"""Full structured extraction from profile text (regex + spaCy; no guessing)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from profile_backend.metadata_light import LightMetadata, extract_light_metadata
from profile_backend.nlp_utils import get_nlp

_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{2,6}\b"
)

# Label -> normalized key (internal)
_LABEL_ALIASES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^name\b", re.I), "name"),
    (re.compile(r"^(full\s*)?name\b", re.I), "name"),
    (re.compile(r"^gender\b", re.I), "gender"),
    (re.compile(r"^date\s*of\s*birth\b", re.I), "dob"),
    (re.compile(r"^d\.?o\.?b\.?\b", re.I), "dob"),
    (re.compile(r"^birth\s*place\b", re.I), "birth_place"),
    (re.compile(r"^place\s*of\s*birth\b", re.I), "birth_place"),
    (re.compile(r"^birth\s*time\b", re.I), "birth_time"),
    (re.compile(r"^time\s*of\s*birth\b", re.I), "birth_time"),
    (re.compile(r"^height\b", re.I), "height"),
    (re.compile(r"^religion\b", re.I), "religion_caste"),
    (re.compile(r"^caste\b", re.I), "religion_caste"),
    (re.compile(r"^religion\s*[&/]\s*caste\b", re.I), "religion_caste"),
    (re.compile(r"^(mobile|phone|contact|tel\.?)\b", re.I), "contact_number"),
    (re.compile(r"^e-?mail\b", re.I), "email"),
    (re.compile(r"^address\b", re.I), "address"),
    (re.compile(r"^occupation\b", re.I), "occupation_work"),
    (re.compile(r"^work\b", re.I), "occupation_work"),
    (re.compile(r"^job\b", re.I), "occupation_work"),
    (re.compile(r"^salary\b", re.I), "salary"),
    (re.compile(r"^income\b", re.I), "salary"),
    (re.compile(r"^education\b", re.I), "education"),
    (re.compile(r"^qualification\b", re.I), "education"),
    (re.compile(r"^father\s*name\b", re.I), "father_name"),
    (re.compile(r"^father\b", re.I), "father_name"),
    (re.compile(r"^father\s*occupation\b", re.I), "father_occupation"),
    (re.compile(r"^mother\s*name\b", re.I), "mother_name"),
    (re.compile(r"^mother\b", re.I), "mother_name"),
    (re.compile(r"^mother\s*occupation\b", re.I), "mother_occupation"),
    (re.compile(r"^hobbies?\b", re.I), "hobbies"),
    (re.compile(r"^preferences?\b", re.I), "preferences"),
    (re.compile(r"^diet\b", re.I), "diet_preference"),
    (re.compile(r"^brothers?\b", re.I), "brothers"),
    (re.compile(r"^sisters?\b", re.I), "sisters"),
]


@dataclass
class ExtractedFields:
    name: str = ""
    gender: str = ""
    dob: str = ""
    birth_place: str = ""
    birth_time: str = ""
    height: str = ""
    religion_caste: str = ""
    contact_number: str = ""
    email: str = ""
    address: str = ""
    occupation_work: str = ""
    salary: str = ""
    education: str = ""
    father_name: str = ""
    father_occupation: str = ""
    mother_name: str = ""
    mother_occupation: str = ""
    hobbies: str = ""
    preferences: str = ""
    diet_preference: str = ""
    brothers: str = ""
    sisters: str = ""


def _clean_value(s: str) -> str:
    return " ".join(s.strip().split())


def _split_label_lines(text: str) -> Iterable[tuple[str, str]]:
    for raw in text.splitlines():
        line = raw.strip()
        if ":" not in line:
            continue
        key, _, rest = line.partition(":")
        k = key.strip()
        v = _clean_value(rest)
        if not k or not v:
            continue
        yield k, v


def _match_label(key: str) -> str | None:
    for pat, canonical in _LABEL_ALIASES:
        if pat.match(key.strip()):
            return canonical
    return None


def _first_email(text: str) -> str:
    m = _EMAIL_RE.search(text)
    return m.group(0) if m else ""


def _first_phone(text: str) -> str:
    for m in _PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if len(digits) >= 8:
            return m.group(0).strip()
    return ""


def _person_names(text: str) -> list[str]:
    nlp = get_nlp()
    doc = nlp(text[:100_000])
    return [e.text.strip() for e in doc.ents if e.label_ == "PERSON"]


def explicit_name_from_text(text: str) -> str:
    """Prefer a line like Name: ... for rename (avoids NER false positives)."""
    for key, val in _split_label_lines(text):
        if _match_label(key) == "name" and val:
            return val
    return ""


def primary_person_name(text: str) -> str:
    """First PERSON entity if no explicit Name: line."""
    if (explicit := explicit_name_from_text(text)):
        return explicit
    names = _person_names(text)
    # Skip common false positives next to labels
    bad = {"gender", "male", "female", "name", "date"}
    for n in names:
        if n.strip().lower() not in bad:
            return n
    return ""


def extract_fields(text: str, light: LightMetadata | None = None) -> ExtractedFields:
    """
    Populate fields only from document content.
    Uses label lines, then regex; spaCy PERSON only for name if still empty.
    """
    ex = ExtractedFields()
    if light:
        if light.date_of_birth:
            ex.dob = light.date_of_birth
        if light.gender:
            ex.gender = light.gender

    for key, val in _split_label_lines(text):
        canon = _match_label(key)
        if not canon:
            continue
        current = getattr(ex, canon, "")
        if not current:
            setattr(ex, canon, val)

    em = _first_email(text)
    if em and not ex.email:
        ex.email = em

    ph = _first_phone(text)
    if ph and not ex.contact_number:
        ex.contact_number = ph

    if not ex.name:
        persons = _person_names(text)
        if persons:
            ex.name = persons[0]

    # If light metadata had better dob/gender and line parse missed
    if light:
        if light.date_of_birth and not ex.dob:
            ex.dob = light.date_of_birth
        if light.gender and not ex.gender:
            ex.gender = light.gender

    return ex


def run_full_extraction(text: str) -> tuple[ExtractedFields, LightMetadata]:
    """Run light metadata + full extraction (single-shot helper)."""
    light = extract_light_metadata(text)
    fields = extract_fields(text, light=light)
    return fields, light
