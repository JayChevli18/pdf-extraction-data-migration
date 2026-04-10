"""Unit tests for Google cloud runtime config validation."""

import unittest

from profile_backend.src.profile_backend.application.google_cloud_config import (
    GoogleCloudRuntimeConfig,
    validate_cloud_config,
)


class TestGoogleCloudConfig(unittest.TestCase):
    def test_validate_cloud_config_ok(self):
        cfg = GoogleCloudRuntimeConfig(
            google_drive_creds_json="/tmp/drive.json",
            google_sheets_creds_json="/tmp/sheets.json",
            google_upload_creds_json="/tmp/upload.json",
            gdrive_inbox_folder_id="a",
            gdrive_root_folder_id="b",
            gsheets_spreadsheet_id="c",
            gsheets_sheet_name="Sheet1",
            gdrive_share_with_emails="",
        )
        validate_cloud_config(cfg)

    def test_validate_cloud_config_missing(self):
        cfg = GoogleCloudRuntimeConfig(
            google_drive_creds_json="",
            google_sheets_creds_json="/x",
            google_upload_creds_json="/y",
            gdrive_inbox_folder_id="a",
            gdrive_root_folder_id="b",
            gsheets_spreadsheet_id="c",
            gsheets_sheet_name="Sheet1",
            gdrive_share_with_emails="",
        )
        with self.assertRaises(RuntimeError) as ctx:
            validate_cloud_config(cfg)
        self.assertIn("Drive", str(ctx.exception))
