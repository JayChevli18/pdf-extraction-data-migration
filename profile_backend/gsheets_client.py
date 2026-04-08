"""Google Sheets operations for cloud mode."""

from __future__ import annotations

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


def build_sheets_service(creds_json_path: str):
    creds = Credentials.from_service_account_file(creds_json_path, scopes=SHEETS_SCOPES)
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

