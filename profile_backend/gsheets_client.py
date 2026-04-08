"""Google Sheets operations for cloud mode."""

from __future__ import annotations

from googleapiclient.discovery import build

from profile_backend.google_auth import load_google_credentials

SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


def build_sheets_service(creds_json_path: str):
    creds = load_google_credentials(creds_json_path, scopes=SHEETS_SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def append_row(
    service,
    spreadsheet_id: str,
    sheet_name: str,
    row_values: list[object],
) -> None:
    range_name = f"{sheet_name}!A:Z"
    body = {"values": [row_values]}
    (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )

