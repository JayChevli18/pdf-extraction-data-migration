"""Domain ID generation for profile records."""

from __future__ import annotations

import secrets
from datetime import datetime


def generate_profile_id(dob_iso: str | None) -> str:
    if dob_iso and len(dob_iso) >= 10:
        try:
            dt = datetime.strptime(dob_iso[:10], "%Y-%m-%d")
            ymd = dt.strftime("%Y%m%d")
        except ValueError:
            ymd = datetime.now().strftime("%Y%m%d")
    else:
        ymd = datetime.now().strftime("%Y%m%d")
    suffix = secrets.randbelow(10_000)
    return f"BIO{ymd}{suffix:04d}"
