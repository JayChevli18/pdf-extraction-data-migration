"""Row model aligned with spreadsheet columns."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any


# Column order matches user specification
SHEET_COLUMNS = [
    "ID",
    "Name",
    "Gender",
    "Date of Birth (DOB)",
    "Birth Place",
    "Birth Time",
    "Height",
    "Religion & Caste",
    "Contact Number",
    "Email",
    "Address",
    "Occupation / Work",
    "Salary",
    "Education",
    "Father Name",
    "Father Occupation",
    "Mother Name",
    "Mother Occupation",
    "Hobbies",
    "Preferences",
    "Diet Preference",
    "Brothers",
    "Sisters",
    "Drive Link",
    "Upload Date",
    "Year",
]


@dataclass
class ProfileRecord:
    """One spreadsheet row (final columns)."""

    id: str
    name: str
    gender: str
    dob: str
    birth_place: str
    birth_time: str
    height: str
    religion_caste: str
    contact_number: str
    email: str
    address: str
    occupation_work: str
    salary: str
    education: str
    father_name: str
    father_occupation: str
    mother_name: str
    mother_occupation: str
    hobbies: str
    preferences: str
    diet_preference: str
    brothers: str
    sisters: str
    drive_link: str
    upload_date: str
    year: str

    def to_row_list(self) -> list[Any]:
        return [getattr(self, f.name) for f in fields(self)]


def headers_for_sheet() -> list[str]:
    return list(SHEET_COLUMNS)
