"""Google Drive operations used by cloud pipeline."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from profile_backend.src.profile_backend.infrastructure.google.auth import load_google_credentials

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]


@dataclass
class DriveFile:
    id: str
    name: str
    mime_type: str


def build_drive_service(creds_json_path: str):
    creds = load_google_credentials(creds_json_path, scopes=DRIVE_SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_inbox_files(service, inbox_folder_id: str) -> list[DriveFile]:
    mime_pdf = "application/pdf"
    mime_docx = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    query = (
        f"'{inbox_folder_id}' in parents and trashed=false and "
        f"(mimeType='{mime_pdf}' or mimeType='{mime_docx}')"
    )
    files: list[DriveFile] = []
    page_token = None
    while True:
        resp = (
            service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id,name,mimeType)",
                pageToken=page_token,
                pageSize=100,
                orderBy="name",
            )
            .execute()
        )
        for item in resp.get("files", []):
            files.append(DriveFile(id=item["id"], name=item["name"], mime_type=item.get("mimeType", "")))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files


def download_file_bytes(service, file_id: str) -> bytes:
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return fh.getvalue()


def upload_file_to_folder(
    service,
    parent_folder_id: str,
    file_name: str,
    data: bytes,
    mime_type: str | None = None,
) -> DriveFile:
    ext = Path(file_name).suffix.lower()
    # Browsers and HTTP clients often mislabel PDF/DOCX (e.g. text/plain). The upload bytes are still
    # binary; if we pass that wrong type to Drive, the file is stored as plain text and previews break.
    if ext == ".pdf":
        mime_type = "application/pdf"
    elif ext == ".docx":
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif not mime_type:
        mime_type = "application/octet-stream"

    media = MediaIoBaseUpload(io.BytesIO(data), mimetype=mime_type, resumable=False)
    metadata = {"name": file_name, "parents": [parent_folder_id], "mimeType": mime_type}
    created = service.files().create(body=metadata, media_body=media, fields="id,name,mimeType").execute()
    return DriveFile(id=created["id"], name=created["name"], mime_type=created.get("mimeType", mime_type))


def ensure_folder(service, parent_id: str, name: str) -> str:
    safe_name = name.replace("'", "\\'")
    query = (
        f"'{parent_id}' in parents and trashed=false and "
        f"mimeType='application/vnd.google-apps.folder' and name='{safe_name}'"
    )
    resp = service.files().list(q=query, fields="files(id,name)").execute()
    existing = resp.get("files", [])
    if existing:
        return existing[0]["id"]
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
    created = service.files().create(body=meta, fields="id").execute()
    return created["id"]


def move_and_rename_file(service, file_id: str, new_parent_id: str, new_name: str) -> None:
    record = service.files().get(fileId=file_id, fields="parents").execute()
    prev_parents = ",".join(record.get("parents", []))
    service.files().update(
        fileId=file_id,
        addParents=new_parent_id,
        removeParents=prev_parents,
        body={"name": new_name},
    ).execute()


def ensure_share_link(service, file_id: str, share_with_emails: list[str] | None = None) -> str:
    if share_with_emails:
        for email in share_with_emails:
            email = (email or "").strip()
            if not email:
                continue
            perm = {"type": "user", "role": "reader", "emailAddress": email}
            try:
                service.permissions().create(
                    fileId=file_id,
                    body=perm,
                    sendNotificationEmail=False,
                ).execute()
            except Exception:
                # Ignore pre-existing permission or domain restrictions and continue.
                pass
    meta = service.files().get(fileId=file_id, fields="webViewLink").execute()
    return meta.get("webViewLink", "")
