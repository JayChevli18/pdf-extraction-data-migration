import unittest

from profile_backend.src.profile_backend.api.app import create_app


class TestApiSmoke(unittest.TestCase):
    def test_health_endpoint(self):
        app = create_app()
        client = app.test_client()
        resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"status": "ok"})
