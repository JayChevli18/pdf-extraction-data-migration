"""Flask API composed on top of application services."""

from __future__ import annotations

from urllib.parse import unquote

from flask import Flask, jsonify, request
from flask_cors import CORS

from profile_backend.src.profile_backend.core.logging import setup_logging
from profile_backend.src.profile_backend.core.settings import settings

logger = setup_logging()


def create_app() -> Flask:
    app = Flask(__name__)
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    CORS(
        app,
        resources={r"/*": {"origins": origins or "*"}},
        supports_credentials=False,
    )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/process")
    def process():
        from profile_backend.src.profile_backend.application.services.local_processing import (
            list_inbox_files,
            process_inbox,
        )

        before = [str(p) for p in list_inbox_files()]
        records = process_inbox()
        return jsonify({"queued": before, "processed": len(records), "ids": [r.id for r in records]})

    @app.post("/process/<path:name>")
    def process_single(name: str):
        from profile_backend.src.profile_backend.application.services.local_processing import process_one

        path = (settings.inbox_dir / name).resolve()
        if not str(path).startswith(str(settings.inbox_dir.resolve())):
            return jsonify({"error": "invalid path"}), 400
        if not path.is_file():
            return jsonify({"error": "not found"}), 404
        rec = process_one(path)
        return jsonify({"id": rec.id, "name": rec.name})

    @app.post("/cloud/process")
    def cloud_process():
        from profile_backend.src.profile_backend.application.services.cloud_processing import (
            process_cloud_inbox,
        )

        records = process_cloud_inbox()
        return jsonify({"processed": len(records), "ids": [r.id for r in records]})

    @app.post("/cloud/process/<path:file_id_or_name>")
    def cloud_process_by_file(file_id_or_name: str):
        from profile_backend.src.profile_backend.application.services.cloud_processing import (
            process_cloud_one,
        )
        from profile_backend.src.profile_backend.infrastructure.google.drive_client import (
            build_drive_service,
            list_inbox_files as list_cloud_inbox_files,
        )
        from profile_backend.src.profile_backend.infrastructure.google.sheets_client import (
            build_sheets_service,
        )

        drive = build_drive_service(settings.google_drive_creds_json)
        sheets = build_sheets_service(settings.google_sheets_creds_json)
        files = list_cloud_inbox_files(drive, settings.gdrive_inbox_folder_id)
        by_id = {f.id: f for f in files}
        target = by_id.get(file_id_or_name)
        if not target:
            wanted = unquote(file_id_or_name).strip().lower()
            target = next((f for f in files if f.name.strip().lower() == wanted), None)
        if not target:
            return jsonify({"error": "file not found in inbox (by id or exact name)"}), 404
        rec = process_cloud_one(drive, sheets, target.id, target.name, target.mime_type)
        return jsonify({"id": rec.id, "name": rec.name, "drive_link": rec.drive_link})

    @app.post("/cloud/upload")
    def cloud_upload():
        from profile_backend.src.profile_backend.application.services.cloud_processing import (
            upload_to_cloud_inbox,
        )

        uploaded_files = request.files.getlist("files")
        if not uploaded_files:
            return jsonify({"error": "No files provided. Use multipart field name 'files'."}), 400
        if len(uploaded_files) > 10:
            return jsonify({"error": "Maximum 10 files allowed per request."}), 400
        try:
            results = upload_to_cloud_inbox(uploaded_files)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": f"Google Drive upload failed: {exc}"}), 502
        return jsonify({"uploaded": len(results), "files": results}), 201

    return app


def main():
    setup_logging()
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)
