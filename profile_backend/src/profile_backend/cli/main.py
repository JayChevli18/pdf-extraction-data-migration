"""CLI commands for local and cloud processing."""

from __future__ import annotations

from profile_backend.src.profile_backend.application.services.cloud_processing import process_cloud_inbox
from profile_backend.src.profile_backend.application.services.local_processing import process_inbox
from profile_backend.src.profile_backend.core.logging import setup_logging


def run_local() -> int:
    setup_logging()
    process_inbox()
    return 0


def run_cloud() -> int:
    setup_logging()
    process_cloud_inbox()
    return 0
