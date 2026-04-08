"""CLI entry: process inbox once."""

from __future__ import annotations

import argparse
import sys

from profile_backend.src.profile_backend.application.services.local_processing import (
    list_inbox_files,
    process_inbox,
    process_one,
)
from profile_backend.src.profile_backend.core.logging import setup_logging
from profile_backend.src.profile_backend.core.settings import settings


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Profile document pipeline (local storage)")
    p.add_argument(
        "command",
        nargs="?",
        default="process",
        choices=("process", "list"),
        help="process all inbox files, or list inbox",
    )
    p.add_argument(
        "--file",
        "-f",
        help="Process a single file name inside the inbox (optional)",
    )
    args = p.parse_args(argv)

    log = setup_logging()
    if args.command == "list":
        files = list_inbox_files()
        for f in files:
            print(f)
        log.info("Listed %s inbox file(s)", len(files))
        return 0

    if args.file:
        path = settings.inbox_dir / args.file
        if not path.is_file():
            log.error("File not found: %s", path)
            return 1
        process_one(path)
        return 0

    recs = process_inbox()
    log.info("Processed %s file(s)", len(recs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
