import io
import unittest

from profile_backend.src.profile_backend.api.app import create_app


class TestApiSmoke(unittest.TestCase):
    def test_health_endpoint(self):
        app = create_app()
        client = app.test_client()
        resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"status": "ok"})

    def test_cloud_config_register_requires_service_account(self):
        app = create_app()
        client = app.test_client()
        resp = client.post(
            "/cloud/config/register",
            data={
                "gdrive_inbox_folder_id": "inbox1",
                "gdrive_root_folder_id": "root1",
                "gsheets_spreadsheet_id": "sheet1",
            },
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("service_account", resp.get_json().get("error", ""))

    def test_cloud_config_register_creates_config_id(self):
        app = create_app()
        client = app.test_client()
        sa = io.BytesIO(b'{"type": "service_account", "project_id": "demo"}')
        sa.name = "sa.json"
        resp = client.post(
            "/cloud/config/register",
            data={
                "service_account": (sa, "service_account.json"),
                "gdrive_inbox_folder_id": "inbox-folder-id",
                "gdrive_root_folder_id": "root-folder-id",
                "gsheets_spreadsheet_id": "spreadsheet-id",
                "gsheets_sheet_name": "Profiles",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(resp.status_code, 201, msg=resp.get_data(as_text=True))
        body = resp.get_json()
        self.assertIn("config_id", body)
        self.assertEqual(len(body["config_id"]), 36)

        del_resp = client.delete(f"/cloud/config/{body['config_id']}")
        self.assertEqual(del_resp.status_code, 200)
        self.assertTrue(del_resp.get_json().get("deleted"))
