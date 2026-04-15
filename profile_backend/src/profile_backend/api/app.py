"""Flask API composed on top of application services."""

from __future__ import annotations

from urllib.parse import unquote

from flask import Flask, jsonify, request
from flask_cors import CORS

from profile_backend.src.profile_backend.api.google_config_http import require_registered_google_cloud_config
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
        from profile_backend.src.profile_backend.application.google_cloud_config import GoogleCloudRuntimeConfig
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
        cfg = GoogleCloudRuntimeConfig.from_settings()
        try:
            rec = process_cloud_one(drive, sheets, target.id, target.name, target.mime_type, cfg)
        except RuntimeError as exc:
            message = str(exc)
            status = 504 if "timed out" in message.lower() else 502
            return jsonify({"error": message}), status
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

    @app.post("/cloud/tenant/process")
    def cloud_tenant_process():
        from profile_backend.src.profile_backend.application.services.cloud_processing import (
            process_cloud_inbox,
        )

        try:
            cfg = require_registered_google_cloud_config(request)
        except (ValueError, FileNotFoundError) as exc:
            return jsonify({"error": str(exc)}), 400 if isinstance(exc, ValueError) else 404
        try:
            records = process_cloud_inbox(cfg)
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"processed": len(records), "ids": [r.id for r in records]})

    @app.post("/cloud/tenant/process/<path:file_id_or_name>")
    def cloud_tenant_process_by_file(file_id_or_name: str):
        from profile_backend.src.profile_backend.application.google_cloud_config import validate_cloud_config
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

        try:
            cfg = require_registered_google_cloud_config(request)
        except (ValueError, FileNotFoundError) as exc:
            return jsonify({"error": str(exc)}), 400 if isinstance(exc, ValueError) else 404
        try:
            validate_cloud_config(cfg)
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 400

        drive = build_drive_service(cfg.google_drive_creds_json)
        sheets = build_sheets_service(cfg.google_sheets_creds_json)
        files = list_cloud_inbox_files(drive, cfg.gdrive_inbox_folder_id)
        by_id = {f.id: f for f in files}
        target = by_id.get(file_id_or_name)
        if not target:
            wanted = unquote(file_id_or_name).strip().lower()
            target = next((f for f in files if f.name.strip().lower() == wanted), None)
        if not target:
            return jsonify({"error": "file not found in inbox (by id or exact name)"}), 404
        try:
            rec = process_cloud_one(drive, sheets, target.id, target.name, target.mime_type, cfg)
        except RuntimeError as exc:
            message = str(exc)
            status = 504 if "timed out" in message.lower() else 502
            return jsonify({"error": message}), status
        return jsonify({"id": rec.id, "name": rec.name, "drive_link": rec.drive_link})

    @app.post("/cloud/tenant/upload")
    def cloud_tenant_upload():
        from profile_backend.src.profile_backend.application.services.cloud_processing import (
            upload_to_cloud_inbox,
        )

        try:
            cfg = require_registered_google_cloud_config(request)
        except (ValueError, FileNotFoundError) as exc:
            return jsonify({"error": str(exc)}), 400 if isinstance(exc, ValueError) else 404

        uploaded_files = request.files.getlist("files")
        if not uploaded_files:
            return jsonify({"error": "No files provided. Use multipart field name 'files'."}), 400
        if len(uploaded_files) > 10:
            return jsonify({"error": "Maximum 10 files allowed per request."}), 400
        try:
            results = upload_to_cloud_inbox(uploaded_files, cfg)
        except (ValueError, RuntimeError) as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": f"Google Drive upload failed: {exc}"}), 502
        return jsonify({"uploaded": len(results), "files": results}), 201

    @app.post("/cloud/config/register")
    def cloud_config_register():
        """Register Drive/Sheets credentials and folder IDs; returns config_id for subsequent cloud APIs."""
        from profile_backend.src.profile_backend.infrastructure.google.config_store import (
            register_google_cloud_config,
        )

        sa = request.files.get("service_account")
        if not sa:
            return jsonify({"error": "Multipart file 'service_account' is required."}), 400
        client = request.files.get("client_secret")
        drive_f = request.files.get("drive_credentials")
        sheets_f = request.files.get("sheets_credentials")

        def _read_optional(f):
            if f is None:
                return None
            data = f.read()
            return data if data else None

        try:
            config_id = register_google_cloud_config(
                service_account_bytes=sa.read(),
                client_secret_bytes=_read_optional(client),
                drive_credentials_bytes=_read_optional(drive_f),
                sheets_credentials_bytes=_read_optional(sheets_f),
                gdrive_inbox_folder_id=(request.form.get("gdrive_inbox_folder_id") or "").strip(),
                gdrive_root_folder_id=(request.form.get("gdrive_root_folder_id") or "").strip(),
                gsheets_spreadsheet_id=(request.form.get("gsheets_spreadsheet_id") or "").strip(),
                gsheets_sheet_name=(request.form.get("gsheets_sheet_name") or "").strip() or None,
                gdrive_share_with_emails=(request.form.get("gdrive_share_with_emails") or "").strip() or None,
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"config_id": config_id}), 201

    @app.delete("/cloud/config/<config_id>")
    def cloud_config_delete(config_id: str):
        from profile_backend.src.profile_backend.infrastructure.google.config_store import (
            delete_google_cloud_config,
        )

        if not delete_google_cloud_config(config_id):
            return jsonify({"error": "Unknown config_id."}), 404
        return jsonify({"deleted": True})

    return app


def main():
    setup_logging()
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)
