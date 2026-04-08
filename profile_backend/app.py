"""Optional HTTP API for triggering processing."""

from __future__ import annotations

import logging

from flask import Flask, jsonify

from profile_backend.logging_setup import setup_logging
from profile_backend.cloud_pipeline import process_cloud_inbox, process_cloud_one
from profile_backend.pipeline import list_inbox_files, process_inbox, process_one

logger = setup_logging()


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/process")
    def process():
        """Process all files currently in the inbox."""
        before = [str(p) for p in list_inbox_files()]
        records = process_inbox()
        return jsonify(
            {
                "queued": before,
                "processed": len(records),
                "ids": [r.id for r in records],
            }
        )

    @app.post("/process/<path:name>")
    def process_single(name: str):
        """Process one file by name under the inbox directory."""
        from profile_backend.config import INBOX_DIR

        path = (INBOX_DIR / name).resolve()
        if not str(path).startswith(str(INBOX_DIR.resolve())):
            return jsonify({"error": "invalid path"}), 400
        if not path.is_file():
            return jsonify({"error": "not found"}), 404
        rec = process_one(path)
        return jsonify({"id": rec.id, "name": rec.name})

    @app.post("/cloud/process")
    def cloud_process():
        """Process all files currently in the Google Drive inbox folder."""
        records = process_cloud_inbox()
        return jsonify(
            {
                "processed": len(records),
                "ids": [r.id for r in records],
            }
        )

    @app.post("/cloud/process/<path:file_id_or_name>")
    def cloud_process_one(file_id_or_name: str):
        """Process one Google Drive file by fileId OR by file name (must be in inbox folder)."""
        from profile_backend.config import GOOGLE_CREDS_JSON
        from profile_backend.gdrive_client import build_drive_service, list_inbox_files
        from profile_backend.gsheets_client import build_sheets_service
        from profile_backend.config import GDRIVE_INBOX_FOLDER_ID
        from urllib.parse import unquote

        drive = build_drive_service(GOOGLE_CREDS_JSON)
        sheets = build_sheets_service(GOOGLE_CREDS_JSON)
        files = list_inbox_files(drive, GDRIVE_INBOX_FOLDER_ID)

        # 1) Try by fileId
        by_id = {f.id: f for f in files}
        f = by_id.get(file_id_or_name)

        # 2) Try by exact name match (URL-decoded, case-insensitive)
        if not f:
            wanted = unquote(file_id_or_name).strip()
            wanted_l = wanted.lower()
            for cand in files:
                if cand.name.strip().lower() == wanted_l:
                    f = cand
                    break

        if not f:
            return (
                jsonify(
                    {
                        "error": "file not found in inbox (by id or exact name)",
                        "hint": "If calling by name, URL-encode spaces as %20.",
                    }
                ),
                404,
            )
        rec = process_cloud_one(drive, sheets, f.id, f.name, f.mime_type)
        return jsonify({"id": rec.id, "name": rec.name, "drive_link": rec.drive_link})

    return app


def main():
    setup_logging()
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
