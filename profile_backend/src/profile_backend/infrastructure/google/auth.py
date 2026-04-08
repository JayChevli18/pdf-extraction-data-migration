"""Google auth helper supporting service account and OAuth client credentials."""

from __future__ import annotations

import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as UserCredentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow


def load_google_credentials(
    creds_json_path: str,
    scopes: list[str],
    token_cache_path: str = "token.json",
):
    path = Path(creds_json_path)
    if not path.exists():
        raise RuntimeError(f"Credentials file not found: {creds_json_path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and raw.get("type") == "service_account":
        return ServiceAccountCredentials.from_service_account_file(creds_json_path, scopes=scopes)

    token_path = Path(token_cache_path)
    creds = None
    if token_path.exists():
        creds = UserCredentials.from_authorized_user_file(str(token_path), scopes=scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_json_path, scopes=scopes)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds
